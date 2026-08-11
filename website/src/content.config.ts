// Content collections for the adore website.
// Blog posts live in src/content/blog/*.md and are loaded via the glob loader.
import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    /** Publish date - accepts YYYY-MM-DD strings. */
    date: z.coerce.date(),
    /** Optional last-updated date. */
    updated: z.coerce.date().optional(),
    author: z.string().default("adore"),
    tags: z.array(z.string()).default([]),
    /** Hide from listings/builds while still editable. */
    draft: z.boolean().default(false),
    /** Optional social/share image (path under /public or absolute URL). */
    image: z.string().optional(),
  }),
});

export const collections = { blog };
