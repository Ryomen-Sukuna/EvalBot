from ast import pattern
import base64
import io
from bs4 import BeautifulSoup
import requests

from modules.helpers import command


def upload_img(filePath):
    searchUrl = 'http://www.google.hr/searchbyimage/upload'
    multipart = {'encoded_image': (filePath, open(
        filePath, 'rb')), 'image_content': ''}
    response = requests.post(searchUrl, files=multipart, allow_redirects=False)
    fetchUrl = response.headers['Location']
    return fetchUrl


def fetch_img(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
    }
    response = requests.get('http://www.google.hr/search?tbs=sbi:AMhZZithYYziVfBpTTN57X6ZcbSqTJwUtDboW_1qpQ-WhjZZLSvPzqhgFeZFrd_13OLh88Tt1X72UzeceuDBjTy5MAvqkHlE_1H-1A4dGI0XgCPOWjvNpPoExgteqMI7DQH_1LayaKCo0RuKp9anA9F5ZFIHCDD2YgfdcnyDt9RJfC7KRArt_1dIUVqvxOyEmb0TXDPw4ZvUYknGFbeA0sR0rAb3U064SRpQwG0BmAS6aku_14gDCrelrQcBhirTn39dbY6tuCL03VkWBvDNVrg-6KxoPxM12eu7dbr5NDzcIjmyy7RykEzlmDSyqZaWgKLfVtwcuuEuWByjVA', headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def collect_results(soup):
    results = []
    for result in soup.find_all(class_="jtfYYd"):
        title = result.find(class_='LC20lb').text if result.find(
            class_='LC20lb') else ""
        if not title:
            continue
        url = result.find('a')['href'] if result.find('a') else ""
        description = result.find_all(
            "span")[-1].text if result.find_all("span") else ""
        results.append({'title': title, 'url': url,
                       'description': description})

    images = []
    images_div = soup.find(class_="pvresd LFls2 MBlpC")
    for result in images_div.find_all('img'):
        src = result['src'] if result['src'] else ""
        if not src:
            continue
        byte = src.split(',')[1]
        byte = base64.b64decode(byte)
        images.append(byte)
    return results, images


@command(pattern="reverse")
async def _reverse(e):
    r = await e.get_reply_message()
    if not r or not r.media:
        await e.edit("`Reply to a photo or sticker to reverse it.`")
        return
    if not r.file.name.endswith((".jpg", ".png", ".jpeg", ".bmp", ".webp")):
        await e.edit("`Reply to static a photo or sticker to reverse it.`")
        return
    rp = await e.reply("`Processing...`")
    p = await e.client.download_media(r.media)
    url = upload_img(p)
    soup = fetch_img(url)
    results, images = collect_results(soup)
    if not results:
        await rp.edit("`Couldn't find anything in reverse search.`")
        return
    RESULT = f"**Search Query:**\n`{url}`\n\n**Results:**\n"
    q = 0
    for result in results:
        q += 1
        RESULT += f"`{q}.` [{result['title']}]({result['url']})\n"
        if q == 3:
            break
    album = []
    for image in images:
        album.append(io.BytesIO(image))
    await e.client.send_file(e.chat_id, album, caption=RESULT, reply_to=rp.id)
