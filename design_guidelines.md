{
  "project": "KHOVA AI — Visual Design System Refinement (Phase 1)",
  "scope_guardrails": {
    "do_not_change": [
      "Do NOT redesign/regenerate/alter the existing Khova logo asset.",
      "Do NOT propose new IA/pages. This is a re-theme only.",
      "Keep shadcn/ui (New York) component structure; only retheme tokens + light utility re-tints.",
      "Avoid copying any single competitor UI; use inspiration only for principles."
    ],
    "must_support": [
      "Light + Dark mode token sets",
      "Wizard (10-step) cards, score bars, palette picker, format picker",
      "Dashboard AI-input-first layout",
      "Projects list, Settings, Landing"
    ]
  },
  "brand_attributes": {
    "keywords": [
      "modern",
      "clean",
      "intelligent",
      "premium",
      "minimal",
      "highly readable",
      "original"
    ],
    "personality_translation": {
      "premium": "cool neutrals, crisp borders, restrained shadows, high typographic discipline",
      "intelligent": "clear hierarchy, predictable spacing, strong focus states, calm color",
      "minimal": "white/near-white canvases, low-chroma surfaces, no decorative overload",
      "original": "subtle blue spectral accents + micro-texture/noise; avoid generic teal/amber editorial warmth"
    }
  },
  "inspiration_fusion" : {
    "reference_directions": [
      {
        "source": "shadcn design gallery (Together/Perplexity/Vercel/Brex/Replicate)",
        "take": "tight typography + calm neutrals + strong primary CTA + thin borders + soft elevation"
      },
      {
        "source": "modern AI SaaS dashboards (Promptly-style admin templates)",
        "take": "input-first hero, bento stats, subtle ring focus, dense-but-breathable spacing"
      }
    ],
    "fusion_recipe": "Use Khova royal-blue as the only strong chroma. Pair with ink/navy text, cool-gray surfaces, and a restrained analogous blue→sky gradient only in hero accents (<20% viewport). Add a faint noise overlay to avoid flatness."
  },
  "typography": {
    "font_pairing": {
      "heading_display": {
        "family": "Montserrat",
        "why": "confident, premium SaaS feel; geometric clarity; pairs well with blue identity",
        "usage": "H1/H2, wizard step titles, landing hero headline"
      },
      "ui_body": {
        "family": "Figtree",
        "why": "high readability at small sizes; friendly but modern; great for Indonesian-first UI",
        "usage": "body, labels, helper text, tables"
      },
      "mono": {
        "family": "Roboto Mono",
        "usage": "IDs, export filenames, code-like snippets, token previews"
      }
    },
    "google_fonts_import_replace": {
      "replace_in": "/app/frontend/src/index.css",
      "new_import": "@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Montserrat:wght@500;600;700;800&family=Roboto+Mono:wght@400;500;600&display=swap');",
      "remove": "Gloock + Manrope + IBM Plex Mono imports"
    },
    "tailwind_usage_notes_js": {
      "body_default": "Set body font-family to Figtree.",
      "display_class": "Update .font-display to Montserrat.",
      "mono_class": "Update .font-mono to Roboto Mono.",
      "text_hierarchy": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl font-display font-semibold tracking-tight",
        "h2": "text-base md:text-lg text-muted-foreground",
        "section_title": "text-xl sm:text-2xl font-display font-semibold",
        "body": "text-sm sm:text-base leading-relaxed",
        "small": "text-xs text-muted-foreground"
      }
    }
  },
  "color_system": {
    "notes": [
      "All values are HSL triplets compatible with shadcn tokens.",
      "Primary is Khova royal/deep blue; accents stay in the same hue family (blue→sky).",
      "Keep gradients analogous only and restrained (<20% viewport).",
      "Replace warm teal/amber editorial theme entirely."
    ],
    "light_mode_tokens_root": {
      "--background": "210 33% 99%",
      "--foreground": "222 47% 11%",
      "--card": "0 0% 100%",
      "--card-foreground": "222 47% 11%",
      "--popover": "0 0% 100%",
      "--popover-foreground": "222 47% 11%",

      "--primary": "226 86% 40%",
      "--primary-foreground": "0 0% 100%",

      "--secondary": "214 32% 96%",
      "--secondary-foreground": "222 47% 11%",

      "--muted": "214 32% 96%",
      "--muted-foreground": "215 16% 40%",

      "--accent": "206 92% 92%",
      "--accent-foreground": "226 70% 22%",

      "--destructive": "0 72% 46%",
      "--destructive-foreground": "0 0% 100%",

      "--border": "214 26% 90%",
      "--input": "214 26% 90%",
      "--ring": "226 86% 40%",

      "--radius": "0.85rem",

      "--success": "152 55% 34%",
      "--success-soft": "152 45% 92%",

      "--warning": "34 92% 44%",
      "--warning-soft": "36 90% 92%",

      "--info": "206 92% 44%",
      "--info-soft": "206 92% 92%",

      "--amber": "34 92% 44%",
      "--amber-soft": "36 90% 92%",

      "--ink-2": "222 47% 14%"
    },
    "dark_mode_tokens_dark": {
      "--background": "222 47% 7%",
      "--foreground": "210 40% 96%",
      "--card": "222 47% 9%",
      "--card-foreground": "210 40% 96%",
      "--popover": "222 47% 9%",
      "--popover-foreground": "210 40% 96%",

      "--primary": "214 95% 62%",
      "--primary-foreground": "222 47% 9%",

      "--secondary": "222 30% 14%",
      "--secondary-foreground": "210 40% 96%",

      "--muted": "222 30% 14%",
      "--muted-foreground": "215 20% 70%",

      "--accent": "226 60% 18%",
      "--accent-foreground": "210 40% 96%",

      "--destructive": "0 72% 52%",
      "--destructive-foreground": "0 0% 100%",

      "--border": "222 26% 18%",
      "--input": "222 26% 18%",
      "--ring": "214 95% 62%",

      "--radius": "0.85rem",

      "--success": "152 55% 46%",
      "--success-soft": "152 35% 16%",

      "--warning": "34 92% 56%",
      "--warning-soft": "34 45% 16%",

      "--info": "206 92% 60%",
      "--info-soft": "206 45% 16%",

      "--amber": "34 92% 56%",
      "--amber-soft": "34 45% 16%",

      "--ink-2": "210 40% 92%"
    },
    "khova_blue_primitives_optional": {
      "note": "Optional helper tokens if you want explicit stops for gradients/illustrations (not required by shadcn).",
      "--khova-blue-950": "226 70% 14%",
      "--khova-blue-900": "226 72% 18%",
      "--khova-blue-800": "226 78% 24%",
      "--khova-blue-700": "226 84% 32%",
      "--khova-blue-600": "226 86% 40%",
      "--khova-blue-500": "214 95% 56%",
      "--khova-sky-400": "203 92% 62%",
      "--khova-sky-300": "200 92% 72%",
      "--khova-sky-200": "198 92% 84%"
    }
  },
  "gradients_and_texture": {
    "rules": {
      "max_viewport_coverage": "<20%",
      "allowed_hues": "analogous blues only (deep royal → sky/cyan-blue)",
      "never": [
        "purple/pink combos",
        "gradients on text-heavy reading areas",
        "gradients on small UI elements (<100px)",
        "stacked gradients in same viewport"
      ]
    },
    "approved_gradients": {
      "hero_mist_light": "radial-gradient(900px circle at 12% 0%, hsl(214 95% 56% / 0.14), transparent 55%), radial-gradient(760px circle at 88% 6%, hsl(203 92% 62% / 0.12), transparent 52%)",
      "paper_cool_light": "radial-gradient(700px circle at 15% 0%, hsl(226 86% 40% / 0.10), transparent 55%), radial-gradient(820px circle at 85% 10%, hsl(200 92% 72% / 0.08), transparent 60%)",
      "hero_mist_dark": "radial-gradient(900px circle at 12% 0%, hsl(214 95% 62% / 0.16), transparent 55%), radial-gradient(760px circle at 88% 6%, hsl(203 92% 62% / 0.10), transparent 52%)"
    },
    "noise_overlay": {
      "intent": "Premium anti-flatness; extremely subtle.",
      "css_snippet": ".noise-overlay{position:relative;} .noise-overlay:before{content:'';position:absolute;inset:0;pointer-events:none;background-image:url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"160\" height=\"160\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.9\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"160\" height=\"160\" filter=\"url(%23n)\" opacity=\"0.08\"/></svg>');mix-blend-mode:multiply;opacity:.35;border-radius:inherit;} .dark .noise-overlay:before{mix-blend-mode:screen;opacity:.18;}"
    }
  },
  "component_guidelines": {
    "component_path": {
      "button": "/app/frontend/src/components/ui/button.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "input": "/app/frontend/src/components/ui/input.jsx",
      "textarea": "/app/frontend/src/components/ui/textarea.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "progress": "/app/frontend/src/components/ui/progress.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "sheet_drawer": "/app/frontend/src/components/ui/sheet.jsx",
      "dropdown": "/app/frontend/src/components/ui/dropdown-menu.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "sonner_toast": "/app/frontend/src/components/ui/sonner.jsx",
      "calendar_if_needed": "/app/frontend/src/components/ui/calendar.jsx"
    },
    "buttons": {
      "shape": "Professional / Corporate leaning premium: radius ~12–14px (tokenized via --radius)",
      "variants": {
        "primary": {
          "visual": "solid royal blue",
          "hover": "slightly darker + subtle lift",
          "active": "press scale 0.98",
          "focus": "focus-visible:ring-2 ring-ring/40 ring-offset-2 ring-offset-background",
          "disabled": "opacity-50 cursor-not-allowed"
        },
        "secondary": {
          "visual": "cool-gray surface with border",
          "hover": "border strengthens + background slightly darker",
          "focus": "same ring behavior"
        },
        "ghost": {
          "visual": "transparent",
          "hover": "bg-accent text-accent-foreground",
          "use": "toolbar actions, step navigation"
        },
        "destructive": {
          "visual": "solid red",
          "hover": "darken",
          "focus": "ring-destructive/30"
        }
      },
      "data_testid_examples": [
        "data-testid=\"primary-cta-button\"",
        "data-testid=\"wizard-next-button\"",
        "data-testid=\"project-create-button\""
      ]
    },
    "cards": {
      "default": "bg-card border border-border rounded-[var(--radius)]",
      "elevation": "Use existing .card-elev and .card-elev-hover utilities; keep shadows subtle.",
      "wizard_step_cards": "Prefer border + soft shadow; avoid heavy gradients inside cards."
    },
    "inputs": {
      "default": "bg-background border-input",
      "focus": "focus-visible:ring-2 ring-ring/35 ring-offset-2 ring-offset-background",
      "invalid": "border-destructive/60 focus-visible:ring-destructive/25",
      "ai_prompt_input": "Make it taller (min-h-[52px]) with leading-relaxed; include helper text below in muted color."
    },
    "badges": {
      "default": "Use Badge with muted background for neutral tags.",
      "status_badges": {
        "success": "bg-[hsl(var(--success-soft))] text-[hsl(var(--success))] border border-[hsl(var(--success)/0.25)]",
        "warning": "bg-[hsl(var(--warning-soft))] text-[hsl(var(--warning))] border border-[hsl(var(--warning)/0.25)]",
        "info": "bg-[hsl(var(--info-soft))] text-[hsl(var(--info))] border border-[hsl(var(--info)/0.25)]",
        "error": "bg-[hsl(var(--destructive)/0.10)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.25)]"
      }
    },
    "progress_score_bars": {
      "use": "shadcn Progress",
      "style": "Track uses muted; indicator uses primary; for multi-metric bars use info/success/warning tokens but keep saturation controlled."
    }
  },
  "layout_and_spacing": {
    "grid": {
      "app_shell": "Max content width 1120–1200px for landing sections; dashboard can be full-width with 24px gutters.",
      "mobile_first": "Single column by default; introduce 2-col at md, 3-col at lg for bento stats/cards.",
      "wizard": "Sticky step header on desktop; on mobile use horizontal scroll tabs (ScrollArea) for steps."
    },
    "spacing_system": {
      "rule": "Use 2–3x more whitespace than current warm editorial theme.",
      "recommended": [
        "Section padding: py-10 sm:py-14",
        "Card padding: p-4 sm:p-6",
        "Form spacing: gap-3 sm:gap-4",
        "Wizard step spacing: space-y-6"
      ]
    }
  },
  "motion_microinteractions": {
    "principles": [
      "No transition:all. Only transition colors/shadows/opacity.",
      "Buttons: hover lift (shadow) + active press (scale-98).",
      "Cards: hover shadow increase + border tint.",
      "Wizard: step change uses subtle fade/slide (8–12px)."
    ],
    "recommended_library": {
      "name": "framer-motion",
      "why": "Entrance/step transitions without layout breakage",
      "install": "npm i framer-motion",
      "usage_snippet_js": "import { motion } from 'framer-motion';\n\nexport default function StepPanel({ children }) {\n  return (\n    <motion.div\n      initial={{ opacity: 0, y: 10 }}\n      animate={{ opacity: 1, y: 0 }}\n      exit={{ opacity: 0, y: -8 }}\n      transition={{ duration: 0.18, ease: 'easeOut' }}\n    >\n      {children}\n    </motion.div>\n  );\n}"
    }
  },
  "retint_existing_utilities": {
    "files": ["/app/frontend/src/index.css"],
    "replace": [
      {
        "utility": ".hero-mist",
        "current": "teal + amber radials",
        "new": "Use approved_gradients.hero_mist_light and hero_mist_dark (via .dark override if desired)."
      },
      {
        "utility": ".paper-warmth",
        "current": "amber warmth + blue",
        "new": "Rename conceptually to .paper-cool (optional) or keep name but retint to blue-only radials."
      }
    ]
  },
  "accessibility": {
    "contrast": [
      "Primary button text must remain white in light mode; in dark mode primary-foreground should be near-background for glare control.",
      "Muted text must still pass AA on background for body sizes; keep muted-foreground >= ~40% lightness in light mode."
    ],
    "focus": "Always visible focus ring using --ring; never remove outline without replacement.",
    "reduced_motion": "Respect prefers-reduced-motion: reduce durations to 0 and remove y-translation."
  },
  "data_testid_policy": {
    "rule": "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
    "examples": [
      "data-testid=\"ai-prompt-input\"",
      "data-testid=\"wizard-step-tabs\"",
      "data-testid=\"wizard-score-progress\"",
      "data-testid=\"export-download-button\"",
      "data-testid=\"settings-save-button\"",
      "data-testid=\"projects-search-input\""
    ]
  },
  "image_urls": {
    "note": "No new brand imagery required for this refinement. Prefer abstract/product UI screenshots already in app. If you need a landing hero illustration, use a subtle abstract blue gradient SVG (no photos) to avoid brand mismatch.",
    "optional": []
  },
  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css: replace font imports + body font + .font-display/.font-mono families.",
    "Replace :root token block with the provided light_mode_tokens_root values.",
    "Add a new .dark { ... } token block using dark_mode_tokens_dark.",
    "Retint .hero-mist and .paper-warmth utilities to the provided blue-only radial gradients; ensure gradients remain decorative and not behind dense text.",
    "Do NOT add .App { text-align:center } (currently safe).",
    "Ensure all buttons/inputs/links and key info elements include data-testid attributes across the app.",
    "Keep shadows subtle; rely on borders + whitespace for premium feel.",
    "If adding motion, use framer-motion with short durations and respect prefers-reduced-motion."
  ],
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
