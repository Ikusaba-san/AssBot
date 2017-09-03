import os
import asyncio
import datetime
from pathlib import Path
from itertools import cycle

import aiohttp
import discord
from discord.ext import commands

from utils import time


class Context(commands.Context):
    @property
    def session(self):
        return self.bot.session


class Bot(commands.Bot):
    def __init__(self):
        def get_prefix(bot, message):
            return message.author.name[0]

        super().__init__(command_prefix=get_prefix,
                         game=discord.Game(name="yes"))

        self.session = aiohttp.ClientSession(loop=self.loop)

        startup_extensions = [x.stem for x in Path('cogs').glob('*.py')]
        for extension in startup_extensions:
            try:
                self.load_extension(f'cogs.{extension}')
            except Exception as e:
                error = f'{extension}\n {type(e).__name__}: {e}'
                print(f'Failed to load extension {error}')

        self.loop.create_task(self.cyc())
        self.loop.create_task(self.init())
        for command in (self._load, self._unload, self._reload):
            self.add_command(command)

    async def init(self):
        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

    @property
    def uptime(self):
        delta = datetime.datetime.utcnow() - self.start_time
        return time.human_time(delta.total_seconds())

    def _do_cleanup(self):
        self.session.close()
        super()._do_cleanup()

    async def on_ready(self):
        self.blob_guild = self.get_guild(328873861481365514)
        self.contrib_role = discord.utils.get(self.blob_guild.roles, id=352849291733237771)
        await self.http.send_message(352011026738446336, "I'm up!")
        print(f'Logged in as {self.user}')
        print('-------------')

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        if ctx.prefix is not None:
            ctx.command = self.all_commands.get(ctx.invoked_with.lower())
            await self.invoke(ctx)

    async def cyc(self):
        await self.wait_until_ready()
        await asyncio.sleep(3)
        guild = self.blob_guild
        for member in cycle(self.contrib_role.members):
            await guild.me.edit(nick=member.name.upper())
            await asyncio.sleep(15)

    @commands.command(name='load')
    async def _load(self, ctx, *, module: str):
        """Loads a module."""

        module = f'cogs.{module}'
        try:
            self.load_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send(f'{type(e).__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(name='reload')
    async def _reload(self, ctx, *, module: str):
        """Reloads a module."""

        module = f'cogs.{module}'
        try:
            self.unload_extension(module)
            self.load_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send(f'{type(e).__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(name='unload')
    async def _unload(self, ctx, *, module: str):
        """Unloads a module."""

        module = f'cogs.{module}'
        try:
            self.unload_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send(f'{type(e).__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')


if __name__ == '__main__':
    bot = Bot()
    token = os.environ["TOKEN"]
    bot.run(token)
