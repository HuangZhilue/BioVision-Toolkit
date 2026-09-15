import re

with open("bioclip.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Insert Token Input Card before Image Upload Card
token_card = """
        <div class="card">
            <div class="form-group" style="margin-bottom: 0;">
                <label for="apiToken">iNaturalist API Token (在线深度识别所需，如只用离线识别可留空)</label>
                <input type="text" id="apiToken" class="input-field" placeholder="在此输入您的 API Token...">
                <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
                    要获取 Token，请登录 <a href="https://www.inaturalist.org/users/api_token" target="_blank" style="color: var(--primary);">iNaturalist</a>。
                </p>
            </div>
        </div>
"""
# Find the first card (which is the upload card)
content = content.replace('<div class="card">', token_card + '\n        <div class="card">', 1)

# 2. Add apiToken to JavaScript variable declarations
content = content.replace("const imageInput = document.getElementById('imageInput');", 
                          "const apiTokenInput = document.getElementById('apiToken');\n        const imageInput = document.getElementById('imageInput');")

# 3. Add token restore logic
token_restore = """
        // Restore token from localStorage
        const savedToken = localStorage.getItem('inat_token');
        if (savedToken) {
            apiTokenInput.value = savedToken;
        }
"""
content = content.replace("let selectedFile = null;", "let selectedFile = null;\n" + token_restore)

# 4. Modify displayResults to append the Online ID button
# Replace the ending of displayResults
online_btn_logic = """
            resultsContainer.innerHTML += `
                <div style="grid-column: 1/-1; text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--border);">
                    <p style="color: var(--text-muted); margin-bottom: 1rem;">对离线识别结果不满意？</p>
                    <button id="onlineSubmitBtn" class="btn secondary-btn" style="margin: 0 auto;">
                        <span class="online-btn-text">🌐 尝试 iNaturalist 在线深度识别</span>
                        <div class="loading-spinner online-spinner"></div>
                    </button>
                </div>
            `;
            
            document.getElementById('onlineSubmitBtn').addEventListener('click', performOnlineIdentification);
        }
"""
content = re.sub(r'\}\)\.join\(\'\'\);\s+\}', "}).join('');" + online_btn_logic, content)

# 5. Add performOnlineIdentification and displayOnlineResults functions
online_functions = """
        async function performOnlineIdentification() {
            const token = apiTokenInput.value.trim();
            if (!token) {
                showError('在线识别需要填写 iNaturalist API Token，请在上方填写。');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                return;
            }
            if (!selectedFile) return;

            localStorage.setItem('inat_token', token);

            hideError();
            const onlineBtn = document.getElementById('onlineSubmitBtn');
            const onlineBtnText = onlineBtn.querySelector('.online-btn-text');
            const onlineSpinner = onlineBtn.querySelector('.online-spinner');
            
            onlineBtn.disabled = true;
            onlineBtnText.textContent = '在线请求中...';
            onlineSpinner.style.display = 'block';

            const formData = new FormData();
            formData.append('image', selectedFile);

            let url = 'https://api.inaturalist.org/v2/taxa/suggest?source=visual&taxon_id=3&fields=all';
            if (selectedLat !== null && selectedLng !== null) {
                formData.append('lat', selectedLat.toString());
                formData.append('lng', selectedLng.toString());
            }

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Authorization': token },
                    body: formData
                });

                if (!response.ok) {
                    let errorMessage = `API Error: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        if (errorData.errors && errorData.errors.length > 0) {
                            errorMessage = errorData.errors.map(e => e.message || JSON.stringify(e)).join(', ');
                        } else if (errorData.error) {
                            errorMessage = errorData.error;
                        }
                    } catch (e) {}
                    throw new Error(errorMessage);
                }

                const data = await response.json();
                displayOnlineResults(data.results);
            } catch (err) {
                showError('在线识别失败: ' + err.message);
                onlineBtn.disabled = false;
                onlineBtnText.textContent = '🌐 尝试 iNaturalist 在线深度识别';
                onlineSpinner.style.display = 'none';
            }
        }

        function displayOnlineResults(results) {
            resultsContainer.innerHTML = '<h3 style="grid-column: 1/-1; color: var(--primary); margin-bottom: 1rem;">🌐 iNaturalist 在线识别结果</h3>';
            
            if (!results || results.length === 0) {
                resultsContainer.innerHTML += '<p style="color: var(--text-muted); grid-column: 1/-1; text-align: center;">未找到匹配的鸟类物种。</p>';
                return;
            }

            resultsContainer.innerHTML += results.slice(0, 8).map(result => {
                const taxon = result.taxon;
                const score = (result.score || 0).toFixed(2);
                const scorePercent = Math.min(100, Math.max(0, score));
                const defaultPhoto = (taxon.default_photo && taxon.default_photo.medium_url) ? taxon.default_photo.medium_url : 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMzMzQxNTUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZmlsbD0iIzY0NzQ4YiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGFsaWdubWVudC1iYXNlbGluZT0ibWlkZGxlIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
                
                return `
                    <div class="result-card">
                        <div class="result-img-wrapper">
                            <img class="result-img" src="${defaultPhoto}" alt="${taxon.name}">
                        </div>
                        <div class="result-info">
                            <div class="taxon-name">${taxon.preferred_common_name || taxon.name}</div>
                            <div class="common-name">${taxon.name}</div>
                            
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${scorePercent}%"></div>
                            </div>
                            <div class="score-text">置信度: ${scorePercent}%</div>
                        </div>
                    </div>
                `;
            }).join('');
            
            resultsContainer.innerHTML += `
                <div style="grid-column: 1/-1; text-align: center; margin-top: 2rem;">
                    <button class="btn secondary-btn" onclick="document.getElementById('submitBtn').click()" style="margin: 0 auto;">返回重新进行本地离线识别</button>
                </div>
            `;
        }
"""
content = content.replace("</script>", online_functions + "\n    </script>")

with open("bioclip.html", "w", encoding="utf-8") as f:
    f.write(content)
