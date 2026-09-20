from typing import Any

from aiohttp import ClientTimeout, ClientError
from attr import dataclass
from mautrix.types import TextMessageEventContent, MessageType, Format
from maubot import Plugin, MessageEvent
from maubot.handlers import command


@dataclass
class UrbanData:
    url: str
    definition: str
    example: str
    word: str


class UrbautrixBot(Plugin):
    url = "https://api.urbandictionary.com/v0/define"
    headers = {"User-Agent": "UrbautrixBot/1.0.0"}

    @command.new(name="urban", aliases=["ud"], help="Get a definition from Urban Dictionary")
    @command.argument("query", pass_raw=True, required=True)
    async def test(self, evt: MessageEvent, query: str) -> None:
        await evt.mark_read()
        if not query:
            await evt.reply("> **Usage:** !urban <query>")
            return

        data = await self._get_definition(query)
        if not data:
            return
        urban_data = await self._parse_definition(data)
        if not urban_data:
            await evt.reply(f"> Failed to find results for **{query}**")
            return
        content = await self._prepare_message(urban_data)
        await evt.reply(content)

    async def _get_definition(self, query: str) -> Any:
        params = {
            "term": query
        }
        timeout = ClientTimeout(total=20)
        try:
            response = await self.http.get(
                self.url,
                timeout=timeout,
                params=params,
                headers=self.headers,
                raise_for_status=True
            )
            return await response.json()
        except ClientError as e:
            self.log.error(f"Connection failed: {e}")
            return ""

    async def _parse_definition(self, data: Any) -> UrbanData | None:
        if not data["list"]:
            return None
        return UrbanData(
            url=data["list"][0]["permalink"],
            definition=(
                data["list"][0]["definition"]
                .replace("]", "")
                .replace("[", "")
                .replace("\r\n", "<br>")
            ),
            example=(
                data["list"][0]["example"]
                .replace("]", "")
                .replace("[", "")
                .replace("\r\n", "<br>")
            ),
            word=data["list"][0]["word"]
        )

    async def _prepare_message(self, data: UrbanData) -> TextMessageEventContent:
        body = (
            f"> [**{data.word}**]({data.url})  \n>  \n"
            f"> {data.definition}  \n>  \n"
            f"> > *{data.example}*  \n>  \n"
            f"> **Results from Urban Dictionary**"
        )
        html = (
            "<blockquote>"
            f"<a href=\"{data.url}\"><b>{data.word}</b></a><br>"
            f"{data.definition}<br>"
            f"<blockquote><i>{data.example}</i></blockquote>"
            "<p><b><sub>Results from Urban Dictionary</sub></b></p>"
            "</blockquote>"
        )

        return TextMessageEventContent(
            msgtype=MessageType.NOTICE,
            format=Format.HTML,
            body=body,
            formatted_body=html
        )
