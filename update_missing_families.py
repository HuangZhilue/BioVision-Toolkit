import json
import asyncio
import aiohttp
import os

async def fetch_taxon_id(session, sci_name):
    url = f"https://api.inaturalist.org/v1/taxa?q={sci_name}&rank=species"
    for _ in range(3):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    for result in results:
                        if result.get("name") == sci_name:
                            return sci_name, result.get("id")
                    return sci_name, None # Not found
                elif response.status == 429:
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"Failed to fetch ID for {sci_name}: {e}")
            await asyncio.sleep(1)
    return sci_name, None

async def fetch_families(session, ids_chunk):
    url = f"https://api.inaturalist.org/v1/taxa/{','.join(ids_chunk)}"
    families = {}
    for _ in range(3):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for result in data.get("results", []):
                        sci_name = result.get("name")
                        for anc in result.get("ancestors", []):
                            if anc.get("rank") == "family":
                                families[sci_name] = anc.get("name")
                                break
                    return families
                elif response.status == 429:
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"Failed to fetch families for chunk: {e}")
            await asyncio.sleep(1)
    return families

async def main():
    with open("china_birds.json", "r", encoding="utf-8") as f:
        birds = json.load(f)
    
    unknowns = [k for k, v in birds.items() if v.get("family") == "Unknown"]
    print(f"Found {len(unknowns)} birds with Unknown family.")
    
    async with aiohttp.ClientSession() as session:
        for i, name in enumerate(unknowns):
            print(f"Processing {i+1}/{len(unknowns)}: {name}")
            _, taxon_id = await fetch_taxon_id(session, name)
            
            if taxon_id:
                families = await fetch_families(session, [str(taxon_id)])
                family = families.get(name)
                if family:
                    birds[name]["family"] = family
                    print(f" -> Found Family: {family}")
                else:
                    print(f" -> Family not found in ancestors")
            else:
                print(f" -> Taxon ID not found")
                
            # Save progressively every 20 items
            if (i + 1) % 20 == 0:
                with open("china_birds.json", "w", encoding="utf-8") as f:
                    json.dump(birds, f, ensure_ascii=False, indent=2)
            
            # Rate limiting (iNat requires < 60 requests per minute)
            await asyncio.sleep(1.2)
            
    with open("china_birds.json", "w", encoding="utf-8") as f:
        json.dump(birds, f, ensure_ascii=False, indent=2)
            
    print("Finished updating families.")

if __name__ == "__main__":
    asyncio.run(main())
