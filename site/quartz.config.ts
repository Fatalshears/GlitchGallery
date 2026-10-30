import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * GlitchGallery - Quartz 4 configuration.
 * This file is copied over the pinned Quartz checkout by scripts/build-site.sh.
 * Palette: Everforest (https://github.com/sainnhe/everforest), medium contrast.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "GlitchGallery",
    pageTitleSuffix: " · GlitchGallery",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl: "fatalshears.github.io/GlitchGallery",
    ignorePatterns: ["private", "templates", ".obsidian"],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Nunito",
        body: "Source Sans 3",
        code: "JetBrains Mono",
      },
      colors: {
        lightMode: {
          light: "#fdf6e3", // bg0
          lightgray: "#e6e2cc", // bg3 - borders, code background
          gray: "#939f91", // grey1 - meta text, graph links
          darkgray: "#5c6a72", // fg - body text
          dark: "#3a464c", // headings
          secondary: "#3c7f68", // darkened aqua - links (WCAG AA on bg0)
          tertiary: "#8da101", // green - hover, visited graph nodes
          highlight: "rgba(141, 161, 1, 0.10)",
          textHighlight: "#dfa00044",
        },
        darkMode: {
          light: "#2d353b", // bg0
          lightgray: "#475258", // bg3
          gray: "#859289", // grey1
          darkgray: "#d3c6aa", // fg
          dark: "#e4dac2", // headings
          secondary: "#a7c080", // green - links
          tertiary: "#83c092", // aqua - hover
          highlight: "rgba(167, 192, 128, 0.10)",
          textHighlight: "#dbbc7f44",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "everforest-light",
          dark: "everforest-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false, mermaid: true }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents({ maxDepth: 3 }),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
