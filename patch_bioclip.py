import re
import os

with open("bioclip.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add head tags
head_insert = """
    <!-- 引入 exifr 库来解析图片的 EXIF GPS 信息 -->
    <script src="https://cdn.jsdelivr.net/npm/exifr/dist/lite.umd.js"></script>
    <!-- 引入 Leaflet 地图 -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
"""
content = content.replace('</head>', head_insert + '\n</head>')

# 2. Add CSS for secondary-btn and rare badge
css_insert = """
        button.secondary-btn {
            background: var(--border);
            color: white;
            font-size: 0.9rem;
            padding: 0.6rem 1rem;
        }
        
        button.secondary-btn:hover:not(:disabled) {
            background: #475569;
        }
        
        .badge-rare {
            position: absolute;
            top: 0.5rem;
            left: 0.5rem;
            background: rgba(100, 116, 139, 0.9);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .input-field {
            width: 100%;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text);
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s ease;
        }
        
        .input-field:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        }
"""
content = content.replace('</style>', css_insert + '\n    </style>')

# 3. Insert location card before submitBtn
html_insert = """
            <h3 style="margin-bottom: 1rem; font-size: 1.1rem; margin-top: 2rem;">区域限制 (省份/定位)</h3>
            <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem;">
                如果指定了省份，系统将降低“该省未曾记录过”的鸟类的排名，以提高本地鸟类识别准确率。
            </p>
            
            <div class="form-group" style="margin-bottom: 1.5rem;">
                <label for="regionSelect">手动选择省份 (优先生效)</label>
                <select id="regionSelect" class="input-field">
                    <option value="">自动判定 (使用下方地图/照片定位)</option>
                    <option value="北京">北京</option>
                    <option value="天津">天津</option>
                    <option value="河北">河北</option>
                    <option value="山西">山西</option>
                    <option value="内蒙古">内蒙古</option>
                    <option value="辽宁">辽宁</option>
                    <option value="吉林">吉林</option>
                    <option value="黑龙江">黑龙江</option>
                    <option value="上海">上海</option>
                    <option value="江苏">江苏</option>
                    <option value="浙江">浙江</option>
                    <option value="安徽">安徽</option>
                    <option value="福建">福建</option>
                    <option value="江西">江西</option>
                    <option value="山东">山东</option>
                    <option value="河南">河南</option>
                    <option value="湖北">湖北</option>
                    <option value="湖南">湖南</option>
                    <option value="广东">广东</option>
                    <option value="广西">广西</option>
                    <option value="海南">海南</option>
                    <option value="重庆">重庆</option>
                    <option value="四川">四川</option>
                    <option value="贵州">贵州</option>
                    <option value="云南">云南</option>
                    <option value="西藏">西藏</option>
                    <option value="陕西">陕西</option>
                    <option value="甘肃">甘肃</option>
                    <option value="青海">青海</option>
                    <option value="宁夏">宁夏</option>
                    <option value="新疆">新疆</option>
                    <option value="台湾">台湾</option>
                    <option value="香港">香港</option>
                    <option value="澳门">澳门</option>
                </select>
            </div>

            <div id="map" style="height: 300px; width: 100%; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid var(--border); z-index: 1;"></div>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem; text-align: center;">您也可以直接在地图上点击以手动选择位置。</p>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <span id="locationStatus" style="font-size: 0.9rem; color: #94a3b8;">未设置位置信息</span>
                <button id="geoBtn" type="button" class="btn secondary-btn">获取当前设备定位</button>
            </div>
"""
content = content.replace('<button id="submitBtn"', html_insert + '\n            <button id="submitBtn"')


# 4. Insert JS logic for map, location, select
js_insert = """
        const regionSelect = document.getElementById('regionSelect');
        const locationStatus = document.getElementById('locationStatus');
        const geoBtn = document.getElementById('geoBtn');
        
        let selectedLat = null;
        let selectedLng = null;
        let marker = null;
        
        // Initialize Leaflet map
        const map = L.map('map').setView([35.8617, 104.1954], 4);
        L.tileLayer('http://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
            subdomains: ['1', '2', '3', '4'],
            maxZoom: 19,
            attribution: '© 高德地图'
        }).addTo(map);

        setTimeout(() => { map.invalidateSize(); }, 500);

        map.on('click', function(e) {
            updateLocation(e.latlng.lat, e.latlng.lng, '已手动在地图上选择位置', true);
        });

        function updateLocation(lat, lng, statusMsg, success) {
            selectedLat = lat;
            selectedLng = lng;
            if (!marker) {
                marker = L.marker([lat, lng]).addTo(map);
            } else {
                marker.setLatLng([lat, lng]);
            }
            map.setView([lat, lng], 10);
            
            locationStatus.textContent = statusMsg;
            locationStatus.style.color = success ? '#34d399' : '#ef4444';
        }

        // Geolocation Button Logic
        geoBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert('您的浏览器不支持地理定位功能');
                return;
            }
            
            locationStatus.textContent = '正在请求定位权限并获取当前位置...';
            locationStatus.style.color = '#fbbf24';
            geoBtn.disabled = true;

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    updateLocation(position.coords.latitude, position.coords.longitude, '已成功获取当前设备定位', true);
                    geoBtn.disabled = false;
                },
                (error) => {
                    locationStatus.textContent = '获取定位失败';
                    locationStatus.style.color = '#ef4444';
                    geoBtn.disabled = false;
                },
                { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
            );
        });
"""
# Replace handleFileSelect completely to add exifr parsing
handle_file_select_new = """
        async function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = (event) => {
                    imagePreview.src = event.target.result;
                    imagePreview.style.display = 'inline-block';
                };
                reader.readAsDataURL(file);
                updateSubmitBtnState();
                
                // Try EXIF GPS
                locationStatus.textContent = '正在读取照片 GPS...';
                locationStatus.style.color = '#fbbf24';
                try {
                    const gps = await exifr.gps(file);
                    if (gps && gps.latitude != null && gps.longitude != null) {
                        updateLocation(gps.latitude, gps.longitude, '已成功读取照片自带 GPS 信息', true);
                    } else {
                        locationStatus.textContent = '照片无 GPS 信息，您可以点击地图或获取当前定位';
                        locationStatus.style.color = '#94a3b8';
                    }
                } catch(error) {
                    locationStatus.textContent = '照片解析失败，请点击地图选择或获取定位';
                    locationStatus.style.color = '#94a3b8';
                }
            }
        }
"""
content = re.sub(r'async function handleFileSelect.*?updateSubmitBtnState\(\);\s+\}\s+\}', handle_file_select_new, content, flags=re.DOTALL)
content = content.replace('let selectedFile = null;', 'let selectedFile = null;\n' + js_insert)

# 5. Update submit payload to include lat, lng, province
submit_payload_addition = """
            if (regionSelect.value) {
                formData.append('province', regionSelect.value);
            }
            if (selectedLat !== null && selectedLng !== null) {
                formData.append('lat', selectedLat.toString());
                formData.append('lng', selectedLng.toString());
            }
"""
content = content.replace("formData.append('image', selectedFile);", "formData.append('image', selectedFile);\n" + submit_payload_addition)

# 6. Update badge logic in displayResults
badge_logic = """
                const badgeHtml = result.is_chinese_bird ? '<div class="badge-china">🇨🇳 中国鸟类</div>' : '';
                const rareBadge = result.is_rare_in_region ? '<div class="badge-rare">⚠️ 区域罕见</div>' : '';
"""
content = content.replace("const badgeHtml = result.is_chinese_bird ? '<div class=\"badge-china\">🇨🇳 中国鸟类</div>' : '';", badge_logic)
content = content.replace("${badgeHtml}", "${badgeHtml}\n                            ${rareBadge}")

with open("bioclip.html", "w", encoding="utf-8") as f:
    f.write(content)
