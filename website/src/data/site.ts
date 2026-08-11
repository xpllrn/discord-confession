// Central content/config for the Confession website.

export const site = {
  name: "confession",
  domain: "confess.adore.rest",
  url: "https://confess.adore.rest",
  tagline: "Anonymous confessions for Discord.",
  description:
    "Confession is Discord's anonymous confession bot. Members submit privately, staff can review, and posts stay anonymous — with replies, filters, and clean setup.",
  shareTitle: "confession",
  shareDescription:
    "Anonymous Discord confessions by the adore.rest network. Submit, review, and post without exposing authors.",
  shareImage: "/brand/og-share.png?v=1",
  prefix: "/",
  invite: "https://discord.com/oauth2/authorize?client_id=1508460938255138981&permissions=274877974528&scope=bot%20applications.commands",
  support: "https://discord.gg/PNDPCfJPFe",
  dashboard: "https://confess.adore.rest",
  docs: "https://confess.adore.rest/faq",
  networkHome: "https://adore.rest",
};

export const seoKeywords = [
  "confession",
  "confession discord bot",
  "confess.adore.rest",
  "adore.rest",
  "discord bot",
  "anonymous discord bot",
].join(", ");

export type NavLink = { label: string; href: string };

export const navLinks: NavLink[] = [
  { label: "docs", href: site.docs },
];

export type Feature = {
  marker: string;
  title: string;
  description: string;
  tag: string;
};

export const features: Feature[] = [
  {
    marker: "##",
    title: "Anonymous posts",
    tag: "privacy",
    description:
      "Members confess without revealing who they are. Authors stay hidden in the channel.",
  },
  {
    marker: "[]",
    title: "Optional review",
    tag: "moderation",
    description:
      "Route submissions through a review channel before they go public.",
  },
  {
    marker: "<>",
    title: "One-command setup",
    tag: "setup",
    description:
      "/setup walks admins through confession and review channels in minutes.",
  },
  {
    marker: "~~",
    title: "Customization panel",
    tag: "control",
    description:
      "Tune avatar, filters, and confession behavior from /panel.",
  },
  {
    marker: "!!",
    title: "Replies & reports",
    tag: "safety",
    description:
      "Keep conversations going with anonymous replies and staff report tools.",
  },
  {
    marker: "**",
    title: "Part of adore.rest",
    tag: "network",
    description:
      "Same network polish as adore and cupid — free to invite, support always nearby.",
  }
];

export type Faq = { id: string; q: string; a: string };

export const faqs: Faq[] = [
  {
    id: "what",
    q: "What is Confession?",
    a: "Confession is an anonymous Discord confession bot. Members submit privately; your server can post them straight away or send them through a review channel first.",
  },
  {
    id: "how",
    q: "How do I set it up?",
    a: "Invite Confession and run /setup. It walks you through confession and review channels. Members then use /confess.",
  },
  {
    id: "anon",
    q: "Can staff see who confessed?",
    a: "Public posts stay anonymous. Owner-only lookup tools exist for abuse handling — see the support server for policy details.",
  },
  {
    id: "filter",
    q: "Can I filter words?",
    a: "Yes. Use /panel to customize filters and other confession settings.",
  },
  {
    id: "support",
    q: "Where do I get help?",
    a: "Join the support server linked in the footer.",
  }
];

export const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqs.map((f) => ({
    "@type": "Question",
    name: f.q,
    acceptedAnswer: { "@type": "Answer", text: f.a },
  })),
};
