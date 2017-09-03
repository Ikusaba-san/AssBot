import io
import os
import json
import textwrap
import traceback
import threading
import asyncio

from contextlib import redirect_stdout

import discord
from discord.ext import commands


class Admin:
    def __init__(self, bot):
        self.bot = bot
        self.bot._last_result = None

    async def __local_check(self, ctx):
        role = discord.utils.get(ctx.guild.roles, id=352849291733237771)
        return role in ctx.author.roles

    @commands.command()
    async def setavatar(self, ctx, link: str):
        """Sets the bot's avatar."""

        async with ctx.session.get(link) as r:
            if r.status == 200:
                try:
                    await ctx.bot.user.edit(avatar=await r.read())
                except Exception as e:
                    await ctx.send(e)
                else:
                    await ctx.send('Avatar set.')
            else:
                await ctx.send('Unable to download image.')

    def cleanup_code(self, content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates code."""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self.bot._last_result,
            'kkk': 'Racist!'
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        code = textwrap.indent(body, '  ')
        to_compile = f'async def func():\n{code}'

        try:
            exec(to_compile, env)
        except SyntaxError as e:
            return await ctx.send(self.get_syntax_error(e))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('🍡')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self.bot._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def gitmerge(self, ctx, *pr_numbers):
        gh_token = os.environ['GH_TOKEN']

        success = []
        failure = []

        data = {'commit_title': f'Merged by {ctx.author}',
                'commit_message': 'Merged from command'}

        headers = {'Content-Type': 'application/json',
                   'Authorization': f"token {gh_token}"}

        for pr in pr_numbers:
            url = f'https://api.github.com/repos/dpy-blobs/AssBot/pulls/{pr}/merge'

            async with ctx.session.put(url, data=json.dumps(data), headers=headers) as resp:
                if resp.status == 200:
                    success.append(pr)
                else:
                    body = await resp.json()
                    failure.append(f"PR #{pr} | Merge Unsuccessful\nMessage: {body["message"]}\nStatus: {resp.status}")
            await asyncio.sleep(5)

        sjoin = ', '.join(success)
        fjoin = '\n'.join(failure)

        if failure and success:
            return await ctx.send(f"PR #(s) **{sjoin}** | Successfully Merged.\n{fjoin}")
        if not failure and success:
            return await ctx.send(f'PR #(s) **{sjoin}** | Successfully Merged.')
        else:
            await ctx.send(fjoin)

    @commands.command(name='threads', hidden=True)
    async def thread_counter(self, ctx):
        await ctx.send(len(threading.enumerate()))

    @commands.command()
    async def cleanup(self, ctx, limit: int = 100):
        """Cleans up the bot's messages."""

        prefixes = tuple(ctx.bot.command_prefix(ctx.bot, ctx.message))

        def check(m):
            return m.author == ctx.me or m.content.startswith(prefixes)

        deleted = await ctx.purge(limit=limit, check=check)
        await ctx.send(f'Cleaned up {len(deleted)} messages.')


def setup(bot):
    bot.add_cog(Admin(bot))
