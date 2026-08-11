---
title: "How to Protect Your Discord Server from Nukes and Raids"
description: "A practical, step-by-step guide to securing your Discord server against nukes and raids using anti-nuke and anti-raid protection, whitelists and trusted admins."
date: 2026-06-02
author: "adore"
tags: ["security", "guide", "anti-nuke", "anti-raid", "moderation"]
draft: false
image: "/blog/discord-nuke-raid-protection.png"
---

A single compromised admin account can wipe out months of work in seconds -
deleted channels, mass bans, renamed roles, spam webhooks. These attacks are
called **nukes** and **raids**, and every growing Discord community is a target
eventually. The good news: with the right setup, most of this is preventable.

This guide walks through exactly how nukes and raids work, and how to lock your
server down using **adore**'s built-in security suite. No prior security
experience needed.

<!-- IMAGE: hero / cover image showing a Discord server being protected.
     Suggested path: /public/blog/discord-nuke-raid-protection.png
     Then reference it here, e.g.:
     ![adore protecting a Discord server](/blog/discord-nuke-raid-protection.png)
-->

## what is a discord nuke?

A **nuke** is a destructive attack carried out by someone who already has
elevated permissions - usually a rogue admin, a compromised account, or a
malicious bot that was added with too many permissions. In a matter of seconds, a
nuke can:

- Mass-delete channels and categories
- Mass-ban or kick members
- Delete or create roles to strip everyone's access
- Spam webhooks to flood channels
- Ping `@everyone` repeatedly

Because the attacker has permission to do these things, normal moderation won't
stop them. You need a system that watches for the *pattern* of abuse and reacts
automatically.

## what is a raid?

A **raid** is the opposite problem: a flood of accounts joining at once, usually
to spam, scam, or harass. Raiders often use freshly created accounts with no
avatar, or a wave of bots added by a single bad actor. The defense here is to
spot suspicious joins and stop them at the door.

<!-- IMAGE: a diagram or screenshot illustrating a raid (many accounts joining).
     Suggested path: /public/blog/discord-raid-example.png
     ![Example of a Discord raid](/blog/discord-raid-example.png)
-->

## the 3 layers of a secure server

Good security isn't one switch - it's layers that back each other up:

1. **Trusted people** - decide who is allowed to make dangerous changes.
2. **Anti-nuke** - limit how much damage any one account can do.
3. **Anti-raid** - filter out suspicious accounts before they cause trouble.

Let's set up each one. Every command below uses adore's default prefix `,` - you
can change it per server.

## step 1: lock down who has power

Before touching anti-nuke, reduce your attack surface:

- **Audit your admins.** Anyone with Administrator can bypass channel
  permissions entirely. Keep that list as short as possible.
- **Limit role permissions.** Don't hand out `Manage Server`, `Manage Roles`,
  `Manage Channels`, `Ban Members` or `Manage Webhooks` unless someone truly
  needs them.
- **Enable 2FA for moderation.** In Discord's *Server Settings → Safety Setup*,
  require two-factor authentication for moderator actions. A compromised admin
  account is the most common source of a nuke.

Next, tell adore who your **trusted** people are. Security admins are
automatically immune to anti-nuke and anti-raid, and they're the only ones who
can change your security settings:

```text
,security admin @trusted-user
```

You can review the list any time:

```text
,security admins
```

> Keep this list tiny. The server owner is always immune; everyone else should
> earn their spot.

## step 2: turn on anti-nuke

adore's anti-nuke watches for dangerous actions and punishes anyone who crosses a
limit - unless they're whitelisted or a security admin. Each module takes an
optional `--limit` (how many actions before it triggers) and `--punishment`
(`strip`, `kick` or `ban`).

Enable the core protections:

```text
,antinuke ban on --limit 1 --punishment ban
,antinuke kick on --limit 2 --punishment kick
,antinuke channel on --limit 2 --punishment strip
,antinuke role on --limit 2 --punishment strip
,antinuke webhook on --limit 1 --punishment kick
,antinuke permissions on --limit 1 --punishment ban
,antinuke everyone on --limit 1
```

Here's what each one does:

- **ban / kick** - stops mass bans and kicks. A limit of `1` means one unexpected
  ban triggers the punishment instantly.
- **channel** - covers both channel creation and deletion, so a nuker can't wipe
  or flood your channel list.
- **role** - covers role create and delete, protecting your permission structure.
- **webhook** - blocks mass webhook creation used for spam.
- **permissions** - catches anyone granting dangerous permissions like
  Administrator or Manage Server.
- **everyone** - limits `@everyone` / `@here` abuse.

<!-- IMAGE: screenshot of the ,antinuke overview embed in Discord.
     Suggested path: /public/blog/antinuke-overview.png
     ![adore antinuke overview](/blog/antinuke-overview.png)
-->

Check your full configuration with:

```text
,antinuke overview
```

### whitelisting trusted bots and users

Some bots legitimately create channels or manage roles. Whitelist them so they
don't trip anti-nuke:

```text
,antinuke whitelist @some-bot
,antinuke whitelists
```

Only whitelist accounts you fully trust - a whitelisted account is exempt from
these protections.

## step 3: turn on anti-raid

Anti-raid filters incoming members so a flood of throwaway accounts never gets a
foothold. Each module supports a `--punishment` of `kick` or `ban`.

```text
,antiraid newaccount on --punishment kick
,antiraid avatar on --punishment kick
,antiraid botadd on --punishment ban
```

What these do:

- **newaccount** - removes accounts younger than 7 days, the classic signature of
  throwaway raid accounts.
- **avatar** - removes accounts still using Discord's default avatar.
- **botadd** - removes bots added by anyone who isn't whitelisted, so an attacker
  can't sneak in a malicious bot.

Review it with:

```text
,antiraid overview
```

And whitelist any regulars you don't want filtered (for example a new member with
a young account):

```text
,antiraid whitelist @member
```

<!-- IMAGE: screenshot of the ,antiraid overview embed in Discord.
     Suggested path: /public/blog/antiraid-overview.png
     ![adore antiraid overview](/blog/antiraid-overview.png)
-->

## extra hardening tips

Beyond adore, a few Discord-native habits make a big difference:

- **Raise the verification level.** Set your server to require a verified phone
  or a registered account for a few minutes before members can chat.
- **Use Discord's built-in raid protection.** The Safety Setup panel offers
  activity alerts and join-gating.
- **Set up a logging channel.** You can't respond to what you can't see. Keep an
  audit-log channel so you can review actions after the fact.
- **Back up your structure.** Periodically note your channel and role layout so
  recovery is faster if something does slip through.
- **Review permissions quarterly.** Roles accumulate permissions over time. Trim
  them regularly.

## a quick recovery plan

If you're hit despite your defenses:

1. **Remove the attacker's access first** - anti-nuke's `strip`/`ban` punishment
   usually handles this automatically.
2. **Lock the server down** while you assess the damage.
3. **Check the audit log** to see exactly what was changed and by whom.
4. **Rebuild from your backup** and rotate any tokens or passwords that may have
   leaked.

## wrapping up

Nukes and raids are fast, but they're also predictable - and predictable attacks
are easy to automate against. With trusted admins locked down, anti-nuke limiting
the blast radius, and anti-raid filtering the door, your server is protected
around the clock without you watching it.

Set it up once and let it run.

<p>
  <a href="https://discord.com/oauth2/authorize?client_id=1510215071559847946&permissions=8&integration_type=0&scope=bot">Add adore to your server</a>
  to enable anti-nuke and anti-raid in minutes, or
  <a href="https://wiki.adore.rest">read the docs</a> for the full security reference.
</p>
