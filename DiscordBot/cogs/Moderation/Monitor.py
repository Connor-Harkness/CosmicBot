import asyncio
import datetime

import discord
from discord.ext import commands
from discord import Embed
import datetime

MONITOR_CHANNEL = 698911166206050375
LOGS_CHANNEL = 680847352977686562


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            return m.id





class Monitor(commands.Cog):
    """Monitoring needs"""

    def __init__(self, bot):
        self.bot = bot

    # async def post_member_log(self, member):
    #     now = datetime.datetime.utcnow()
    #     days, r = divmod(int((now - member.created_at).total_seconds()), 86400)
    #     h, r = divmod(r, 3600)
    #     m, s = divmod(r, 60)
    #     e = discord.Embed(title=f'{member} did the intro', description=f'Made {days} days {h:02}:{m:02}:{s:02} ago',
    #                       color=discord.Colour.green())
    #     e.set_thumbnail(url=member.avatar_url)
    #     e.set_footer(text=member.id)
    #     e.timestamp = now
    #     await self.bot.get_channel(LOGS_CHANNEL).send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self.bot.get_channel(MONITOR_CHANNEL)
        await ch.send(f'{member.mention} joined the server.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self.bot.get_channel(MONITOR_CHANNEL)
        await ch.send(f'{member.mention} is no longer on the server.')
    
    async def log(self, logtype, user_id, channel, content, attachments=''):
        await self.bot.db.execute(
            f'INSERT INTO `monitorlog` (`type`, `user_id`, `channel`, `content`, `attachments`) '
            f'VALUES (%s, %s, %s, %s, %s)', (logtype, user_id, channel, content, attachments))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        att = '\n'.join(x.url for x in message.attachments)
        await self.log('delete', message.author.id, message.channel.id, message.content, att)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        
        if before.content != after.content:
            print(f"edit",f", {before.author.id}, {before.channel.id}, {before.content}")
            embed=discord.Embed(title=f"USER: {before.author.name} Edited their message:")
            embed.set_author(name="Message Edit", icon_url="http://google.com/favicon.ico")
            embed.set_thumbnail(url="http://google.com/favicon.ico")
            embed.add_field(name="Previous Message", value=f"{before.content}", inline=False)
            embed.add_field(name="Edited Message", value=f"{after.content}", inline=False)
            embed.set_footer(text=f"Log issued by: {self.bot.user.name} @ {datetime.datetime.now()}")
            ch = self.bot.get_channel(MONITOR_CHANNEL)
            await ch.send(embed=embed)
            await self.log('edit', before.author.id, before.channel.id, before.content)
            
    @commands.Cog.listener()
    async def on_command(self, ctx):
        print(f"on command! {ctx.author.id}, {ctx.channel.id}, {ctx.message.content}")
        embed=discord.Embed(title=f"USER: {ctx.author.name} Used a command:")
        embed.set_author(name="Command", icon_url="http://google.com/favicon.ico")
        embed.set_thumbnail(url=f"{ctx.author.avatar_url}")
        embed.add_field(name="Command", value=f"{ctx.message.content}", inline=False)
        embed.set_footer(text=f"Log issued by: {ctx.author.name} @ {datetime.datetime.now()}")
        ch = self.bot.get_channel(MONITOR_CHANNEL)
        await ch.send(embed=embed)
        await self.log('command', ctx.author.id, ctx.channel.id, ctx.message.content)

    @commands.group(invoke_without_command=True)
    @commands.has_role('Staff')
    async def deletes(self, ctx):
        qry = 'SELECT user_id, content, attachments FROM monitorlog WHERE type="delete" ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No deletes found')

        def callback(page):
            em = discord.Embed(title=f'Recent deletions from anyone (anywhere)')
            for uid, c, a in rows[page * 5:page * 5 + 5]:
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                mem = ctx.guild.get_member(uid)
                em.add_field(name=mem.display_name if mem else uid, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @deletes.command(name='from')
    @commands.has_role('Staff')
    async def deletes_from(self, ctx, member: MemberID):
        member = await self.bot.get_user_info(member)
        qry = f'SELECT content, attachments FROM monitorlog WHERE type="delete" AND user_id={member.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No deletes found')

        def callback(page):
            em = discord.Embed(title=f'Recent deletions from {member}')
            for c, a in rows[page * 5:page * 5 + 5]:
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                em.add_field(name=member.display_name, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @deletes.command(name='in')
    @commands.has_role('Staff')
    async def deletes_in(self, ctx, channel: discord.TextChannel):
        qry = f'SELECT user_id, content, attachments FROM monitorlog WHERE type="delete" AND channel={channel.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No deletes found')

        def callback(page):
            em = discord.Embed(title=f'Recent deletions in {channel}')
            for u, c, a in rows[page * 5:page * 5 + 5]:
                member = ctx.bot.get_user(u)
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                em.add_field(name=member.display_name if member else u, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @commands.group(invoke_without_command=True, name="commands")
    @commands.has_role('Staff')
    async def _commands(self, ctx):
        qry = 'SELECT user_id, content, attachments FROM monitorlog WHERE type="command" ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No commands found')

        def callback(page):
            em = discord.Embed(title=f'Recent commands from anyone (anywhere)')
            for uid, c, a in rows[page * 5:page * 5 + 5]:
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                mem = ctx.guild.get_member(uid)
                em.add_field(name=mem.display_name if mem else uid, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @_commands.command(name='from')
    @commands.has_role('Staff')
    async def commands_from(self, ctx, member: MemberID):
        member = await self.bot.get_user_info(member)
        qry = f'SELECT content, attachments FROM monitorlog WHERE type="command" AND user_id={member.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No commands found')

        def callback(page):
            em = discord.Embed(title=f'Recent commands from {member}')
            for c, a in rows[page * 5:page * 5 + 5]:
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                em.add_field(name=member.display_name, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    @_commands.command(name='in')
    @commands.has_role('Staff')
    async def commands_in(self, ctx, channel: discord.TextChannel):
        qry = f'SELECT user_id, content, attachments FROM monitorlog WHERE type="command" AND channel={channel.id} ' \
              f'ORDER BY id DESC'
        rows = await self.bot.db.fetch(qry)

        if not rows:
            return await ctx.send('No commands found')

        def callback(page):
            em = discord.Embed(title=f'Recent commands in {channel}')
            for u, c, a in rows[page * 5:page * 5 + 5]:
                member = ctx.bot.get_user(u)
                a = '\n' + ' '.join([f'[image {i+1}]({link})' for i, link in enumerate(a.split('\n'))]) if a else ''
                val = c or '-' + a
                em.add_field(name=member.display_name if member else u, value=val[:1024], inline=False)
            em.set_footer(text=f'Page {page+1}/{len(rows)//5+1}')
            return em

        await self.embed_paginator(ctx, callback)

    async def embed_paginator(self, ctx, callback, index=0):
        buttons = ['???', '???', '????', '???']

        msg = await ctx.send(embed=callback(index))
        for button in buttons:
            await msg.add_reaction(button)

        while True:
            try:
                def check(r, u):
                    return u.id == ctx.author.id and r.message.id == msg.id and str(r) in buttons

                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120)
            except asyncio.TimeoutError:
                break
            else:
                await msg.remove_reaction(reaction, user)
                t = buttons.index(str(reaction))
                if t == 0:
                    if index > 0:
                        index -= 1
                        await msg.edit(embed=callback(index))
                elif t == 1:
                    index += 1
                    await msg.edit(embed=callback(index))
                elif t == 2:
                    await msg.edit(embed=callback(index))
                else:
                    break
        await msg.delete()


def setup(bot):
    bot.add_cog(Monitor(bot))
