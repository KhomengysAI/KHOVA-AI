{
  "brand": {
    "name": "Khova AI",
    "positioning": "AI-powered digital product factory (not a chatbot)",
    "brand_attributes": [
      "trustworthy",
      "craftsmanship-focused",
      "premium",
      "calmly confident",
      "fast-but-careful"
    ],
    "visual_metaphor": "A modern factory line: each station is a step; each output is inspected and stamped as ‘ready to sell’.",
    "north_star": "Make the user believe the output quality is exceptional before they click Generate."
  },

  "design_personality": {
    "style_fusion": [
      "Swiss editorial hierarchy (clear grids, left-aligned, strong typographic rhythm)",
      "Premium SaaS polish (Linear-like restraint, Stripe-like clarity)",
      "Craft texture accents (subtle paper/noise only in backgrounds, never behind text blocks)"
    ],
    "do_not": [
      "No transparent backgrounds (ever)",
      "No purple gradients or saturated gradients",
      "No centered ‘marketing poster’ layouts",
      "No ‘chat bubble’ UI as primary metaphor"
    ]
  },

  "typography": {
    "google_fonts": {
      "heading": {
        "family": "Gloock",
        "fallback": "ui-serif, Georgia, serif",
        "usage": "H1/H2 + key ‘craft’ moments (Opportunity score, Export ready stamp)"
      },
      "body": {
        "family": "Manrope",
        "fallback": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        "usage": "UI body, labels, tables, forms"
      },
      "mono": {
        "family": "IBM Plex Mono",
        "fallback": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        "usage": "Citations, URLs, model/provider labels, IDs"
      }
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-normal tracking-tight",
      "h2": "text-xl sm:text-2xl font-normal tracking-tight",
      "subheading": "text-base md:text-lg text-muted-foreground",
      "body": "text-sm sm:text-base leading-relaxed",
      "small": "text-xs sm:text-sm text-muted-foreground",
      "label": "text-xs font-medium tracking-wide uppercase"
    },
    "typesetting_rules": [
      "Left-align all long-form text and tables.",
      "Use heading font sparingly: only for page titles and ‘milestone’ numbers.",
      "Keep line length ~60–80 chars in reading surfaces (QA editor, eBook preview notes)."
    ]
  },

  "color_system": {
    "notes": "Premium light theme by default (Indonesian audience, trust + readability). Dark mode optional later; do not rely on it.",
    "palette_hex": {
      "ink": "#0B1220",
      "ink_2": "#111C2E",
      "paper": "#FBFAF7",
      "paper_2": "#F6F4EE",
      "card": "#FFFFFF",
      "border": "#E6E2D8",
      "muted_text": "#5B6472",

      "primary_ocean": "#0B6E6B",
      "primary_ocean_hover": "#085E5B",
      "primary_ocean_soft": "#D7F2EF",

      "accent_amber": "#C07A2B",
      "accent_amber_soft": "#F6E7D6",

      "info": "#1E5AA8",
      "info_soft": "#DCEBFF",

      "success": "#1F7A4D",
      "success_soft": "#DDF3E7",

      "warning": "#B45309",
      "warning_soft": "#FDE7C7",

      "danger": "#B42318",
      "danger_soft": "#FEE4E2"
    },
    "semantic_tokens_css": {
      "implementation": "Set these in /frontend/src/index.css :root (HSL values) to override shadcn defaults. Keep backgrounds solid.",
      "tokens": {
        "--background": "paper",
        "--foreground": "ink",
        "--card": "card",
        "--card-foreground": "ink",
        "--popover": "card",
        "--popover-foreground": "ink",
        "--primary": "primary_ocean",
        "--primary-foreground": "#FFFFFF",
        "--secondary": "paper_2",
        "--secondary-foreground": "ink",
        "--muted": "paper_2",
        "--muted-foreground": "muted_text",
        "--accent": "primary_ocean_soft",
        "--accent-foreground": "ink_2",
        "--destructive": "danger",
        "--destructive-foreground": "#FFFFFF",
        "--border": "border",
        "--input": "border",
        "--ring": "primary_ocean"
      }
    },
    "gradients": {
      "restriction": "Gradients only as decorative section backgrounds; max 20% viewport; never behind dense text; never on small elements.",
      "allowed_background_gradients": [
        {
          "name": "Ocean Mist",
          "css": "radial-gradient(900px circle at 15% 10%, rgba(11,110,107,0.12), transparent 55%), radial-gradient(700px circle at 85% 0%, rgba(192,122,43,0.10), transparent 50%)",
          "usage": "Landing hero background only"
        },
        {
          "name": "Paper Warmth",
          "css": "radial-gradient(800px circle at 20% 0%, rgba(192,122,43,0.10), transparent 55%), radial-gradient(900px circle at 80% 20%, rgba(30,90,168,0.08), transparent 60%)",
          "usage": "Wizard header strip / dashboard top band"
        }
      ]
    }
  },

  "spacing_grid": {
    "layout": {
      "max_width": "max-w-6xl (marketing), max-w-7xl (dashboard)",
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "section_padding": "py-14 sm:py-18",
      "grid": "12-col on lg; 4-col on mobile; use gap-6 lg:gap-8"
    },
    "rhythm": {
      "stack": "space-y-6 (forms), space-y-10 (sections)",
      "card_padding": "p-4 sm:p-6",
      "dense_table_padding": "py-2.5 px-3"
    }
  },

  "elevation_radius": {
    "radius_tokens": {
      "--radius": "12px (set in index.css)",
      "card": "rounded-xl",
      "button": "rounded-lg",
      "input": "rounded-lg",
      "pill": "rounded-full (badges/toggles only)"
    },
    "shadows": {
      "card": "shadow-[0_1px_0_rgba(11,18,32,0.06),0_12px_30px_rgba(11,18,32,0.06)]",
      "hover": "hover:shadow-[0_1px_0_rgba(11,18,32,0.08),0_18px_44px_rgba(11,18,32,0.10)]",
      "inset": "shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]"
    },
    "borders": {
      "default": "border border-[color:var(--border)]",
      "focus_ring": "focus-visible:ring-2 focus-visible:ring-[color:var(--ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--background)]"
    }
  },

  "components": {
    "component_path": {
      "button": "/app/frontend/src/components/ui/button.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "input": "/app/frontend/src/components/ui/input.jsx",
      "textarea": "/app/frontend/src/components/ui/textarea.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "progress": "/app/frontend/src/components/ui/progress.jsx",
      "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "sheet": "/app/frontend/src/components/ui/sheet.jsx",
      "drawer": "/app/frontend/src/components/ui/drawer.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "popover": "/app/frontend/src/components/ui/popover.jsx",
      "calendar": "/app/frontend/src/components/ui/calendar.jsx",
      "sonner_toast": "/app/frontend/src/components/ui/sonner.jsx",
      "accordion": "/app/frontend/src/components/ui/accordion.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "navigation_menu": "/app/frontend/src/components/ui/navigation-menu.jsx"
    },

    "buttons": {
      "variants": {
        "primary": {
          "tailwind": "bg-[color:var(--primary)] text-white hover:bg-[#085E5B] active:bg-[#074F4D]",
          "shape": "rounded-lg",
          "motion": "transition-colors duration-200; active:scale-[0.98] (apply only on button)"
        },
        "secondary": {
          "tailwind": "bg-[color:var(--secondary)] text-[color:var(--foreground)] border border-[color:var(--border)] hover:bg-[#F0EDE6]",
          "motion": "transition-colors duration-200"
        },
        "ghost": {
          "tailwind": "bg-transparent hover:bg-[color:var(--secondary)]",
          "motion": "transition-colors duration-200"
        },
        "danger": {
          "tailwind": "bg-[#B42318] text-white hover:bg-[#922018]",
          "motion": "transition-colors duration-200"
        }
      },
      "sizes": {
        "sm": "h-9 px-3 text-sm",
        "md": "h-10 px-4 text-sm",
        "lg": "h-11 px-5 text-base"
      },
      "testing": "All buttons must include data-testid (e.g., data-testid=\"landing-primary-cta-button\")."
    },

    "landing_page": {
      "hero_layout": {
        "pattern": "Left copy + right product ‘factory line’ preview card (bento). Mobile: stack with preview below.",
        "hero_background": "Use Ocean Mist gradient on the section wrapper only; keep content cards solid white.",
        "primary_message": "Lead with pain + promise: ‘Turn your knowledge into a sellable digital product—market-informed, quality-checked, export-ready.’",
        "cta": {
          "primary": "Start a product",
          "secondary": "See how it works (scroll anchor)",
          "note": "Login deferred; only show Google sign-in when user clicks Start/Save."
        },
        "above_fold_elements": [
          "H1 + subheading",
          "Single primary CTA",
          "3 proof bullets (speed, citations, export formats)",
          "Mini pipeline preview (10 steps)"
        ]
      },
      "sections": [
        "Trust strip (logos optional; if none, use ‘Built for creators’ + metrics placeholders)",
        "How it works (10-step factory line)",
        "Output formats (3 active + Coming Soon)",
        "Quality promise (QA editor preview)",
        "Final CTA band"
      ]
    },

    "wizard_stepper": {
      "goal": "Make the creation wizard feel like a premium guided factory line with clear states.",
      "layout": {
        "desktop": "Sticky left vertical stepper (w-72) + main content + right preview/inspector panel (w-[420px]) when applicable.",
        "mobile": "Top horizontal stepper (ScrollArea) + content below; preview becomes Drawer/Sheet.",
        "container": "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
      },
      "states": {
        "completed": {
          "visual": "Check icon + muted label; connector line filled with primary_ocean",
          "badge": "Badge variant secondary: ‘Done’"
        },
        "current": {
          "visual": "Primary_ocean dot + subtle glow ring; step title in ink",
          "badge": "Badge: ‘In progress’"
        },
        "locked": {
          "visual": "Gray dot + lock icon; title muted",
          "badge": "Badge: ‘Locked’"
        },
        "error": {
          "visual": "Danger dot + small error text; keep calm (no red floods)",
          "badge": "Badge: ‘Needs attention’"
        }
      },
      "micro_interactions": [
        "On step change: animate content in with framer-motion (y: 8 -> 0, opacity 0 -> 1, duration 0.22).",
        "On completion: brief success toast via Sonner (‘Step completed’).",
        "On locked click: tooltip explaining requirement."
      ],
      "data_testids": {
        "stepper": "wizard-stepper",
        "step_item": "wizard-step-item-{stepKey}",
        "next": "wizard-next-button",
        "back": "wizard-back-button"
      }
    },

    "discover_step": {
      "two_modes": {
        "component": "Tabs",
        "tabs": [
          "I know what I want",
          "I don’t know yet"
        ],
        "pattern": "Each tab shows a Card with 3–6 fields; keep optional fields collapsed under Accordion ‘Add more context’."
      },
      "context_warning": {
        "component": "Alert",
        "tone": "non-blocking",
        "copy": "More context = better research + higher-quality output.",
        "style": "bg-[color:var(--accent)] text-[color:var(--accent-foreground)] border border-[color:var(--border)]"
      },
      "file_upload": {
        "pattern": "Dropzone Card with dashed border; show file chips; never block progress.",
        "testid": "discover-file-upload"
      }
    },

    "market_research_view": {
      "layout": "Split: left Findings (labeled chips) + right Sources table.",
      "findings_labels": {
        "RESEARCH_BACKED": "Badge bg info_soft text info",
        "HYPOTHESIS": "Badge bg accent_amber_soft text accent_amber",
        "ASSUMPTION": "Badge bg secondary text muted"
      },
      "sources_table": {
        "component": "Table",
        "columns": [
          "Source",
          "Type",
          "Key quote",
          "Open"
        ],
        "url_style": "font-mono text-xs text-[#1E5AA8] underline underline-offset-4",
        "row_interaction": "Row hover bg paper_2; open in new tab icon button",
        "testid": "research-sources-table"
      },
      "citations": "Always show citations as clickable URLs; never hide behind tooltips only."
    },

    "profitable_pockets": {
      "layout": {
        "top_controls": "Sticky filter/sort bar with Select + ToggleGroup + search Input.",
        "grid": "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6",
        "compare": "Use Sheet on desktop; Drawer on mobile"
      },
      "opportunity_card": {
        "structure": [
          "Title + niche tag badges",
          "One-line promise",
          "Overall score (large number in heading font)",
          "6 score bars",
          "Actions: Compare, Save, Build this"
        ],
        "score_bars": {
          "component": "Custom (Progress + labels)",
          "bars": [
            "Pain",
            "Worsening",
            "Purchasing Power",
            "Speed",
            "Market Validation",
            "Differentiation"
          ],
          "color_logic": {
            "0-39": "bg warning_soft + indicator warning",
            "40-69": "bg accent_amber_soft + indicator accent_amber",
            "70-100": "bg success_soft + indicator success"
          },
          "testid": "opportunity-score-bar-{metricKey}"
        },
        "actions_testids": {
          "save": "opportunity-save-button-{id}",
          "compare": "opportunity-compare-button-{id}",
          "build": "opportunity-build-button-{id}"
        }
      }
    },

    "positioning_editor": {
      "pattern": "Card with a prominent one-liner input + supporting fields in 2-col grid.",
      "one_liner": {
        "placeholder": "I help X achieve Y without Z",
        "testid": "positioning-one-liner-input"
      }
    },

    "transformation_map": {
      "layout": "Before/After table across 6 categories; each row is editable.",
      "categories": [
        "Identity",
        "Skills",
        "Beliefs",
        "Habits",
        "Environment",
        "Results"
      ],
      "palette_picker": {
        "pattern": "Popover with 6 swatches + HEX input; store per project.",
        "testid": "product-palette-picker"
      }
    },

    "format_selection": {
      "cards": {
        "active": [
          "eBook (PDF)",
          "Spreadsheet (XLSX)",
          "Simple Website"
        ],
        "coming_soon": [
          "Video",
          "Image packs",
          "Workbook",
          "Checklist",
          "Template Pack",
          "Prompt Pack",
          "Toolkit",
          "Social"
        ],
        "pattern": "Card grid; Coming Soon cards are disabled with Badge ‘Coming soon’ and reduced opacity; keep readable."
      },
      "testid": "format-card-{formatKey}"
    },

    "creation_surfaces": {
      "ebook_creator": {
        "layout": "3-panel: Outline/Chapters (left) + Editor (center) + Live Preview (right). Mobile: Tabs for panels.",
        "progress": "Show section-by-section progress like 11/11 using Progress + numeric label.",
        "cover_image": "Use AspectRatio for cover preview; allow upload or AI generate later.",
        "export": "Primary button ‘Export PDF’ with clear disabled/loading states.",
        "testids": {
          "generate_section": "ebook-generate-section-button",
          "export_pdf": "ebook-export-pdf-button",
          "preview": "ebook-live-preview"
        }
      },
      "spreadsheet_creator": {
        "layout": "Left sheet list + right spec preview; generate/download actions top-right.",
        "testids": {
          "generate": "spreadsheet-generate-button",
          "download": "spreadsheet-download-xlsx-button"
        }
      },
      "website_creator": {
        "layout": "Left section editor + right responsive preview iframe; style selector at top.",
        "preview": "Use a Card wrapper around iframe with device toggle buttons.",
        "testids": {
          "style_selector": "website-style-selector",
          "preview_iframe": "website-preview-iframe",
          "export": "website-export-button"
        }
      }
    },

    "qa_editor": {
      "pattern": "Issue list + scoring sliders (1–10) + ‘Apply recommended improvements’ button.",
      "keep_original": "Always allow toggling between improved/original versions via Tabs.",
      "testids": {
        "apply_improvements": "qa-apply-improvements-button",
        "score_slider": "qa-score-slider-{dimensionKey}"
      }
    },

    "dashboard_projects": {
      "projects_list": {
        "pattern": "Table on desktop + Cards on mobile; each row has actions menu.",
        "actions": [
          "New",
          "Continue",
          "Duplicate",
          "Delete",
          "Export"
        ],
        "testids": {
          "new": "projects-new-button",
          "row": "projects-row-{id}",
          "delete": "projects-delete-button-{id}"
        }
      }
    },

    "settings": {
      "language": {
        "ui_language": "Select (default Indonesian)",
        "product_language": "Select (default Indonesian)",
        "testids": {
          "ui_language": "settings-ui-language-select",
          "product_language": "settings-product-language-select"
        }
      },
      "model_provider": {
        "pattern": "Accordion per agent category; each has provider/model Select.",
        "testid": "settings-model-provider"
      }
    },

    "deferred_login": {
      "pattern": "Dialog modal triggered only on generate/save/export.",
      "copy": "Sign in to save and export your product.",
      "testid": "auth-google-signin-button"
    }
  },

  "motion": {
    "library": "framer-motion (already available)",
    "principles": [
      "Fast, subtle, purposeful. No bouncy overshoot.",
      "Animate entrances for step content and cards; avoid animating layout on every render.",
      "Prefer opacity + translateY; avoid heavy blur animations for performance."
    ],
    "recipes": {
      "page_enter": "initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:0.22,ease:[0.2,0.8,0.2,1]}}",
      "card_hover": "hover:translate-y-[-2px] (use transform only on card wrapper) + shadow change; transition-shadow duration-200",
      "loading": "Use Skeleton + Progress; show ‘what is happening’ labels (Researching… Scoring… Generating PDF…)."
    }
  },

  "data_visualization": {
    "libraries": {
      "recharts": {
        "use_cases": [
          "Opportunity score distribution histogram",
          "Radar chart for 6 metrics when comparing 2 opportunities"
        ],
        "style": "Use muted gridlines (#E6E2D8) and primary_ocean for active series; avoid neon colors."
      }
    },
    "empty_states": {
      "pattern": "Card with short explanation + primary CTA; include a small illustration block (solid background, no transparency)."
    }
  },

  "image_urls": {
    "landing_hero": [
      {
        "url": "https://images.unsplash.com/photo-1655157419763-2a6bfc3b78bf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxOTF8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBtaW5pbWFsJTIwb2ZmaWNlJTIwZGVzayUyMGxhcHRvcCUyMGNvZmZlZXxlbnwwfHx8Ymx1ZXwxNzg4ODU0OTg3fDA&ixlib=rb-4.1.0&q=85",
        "description": "Hero side image (optional) for landing: minimal desk + laptop; use as subtle masked background in a Card, not full-bleed."
      }
    ],
    "textures": [
      {
        "url": "https://images.unsplash.com/photo-1711945344720-243fe94b6b99?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwyfHxjcmFmdCUyMHBhcGVyJTIwdGV4dHVyZSUyMGNsb3NlJTIwdXAlMjBtaW5pbWFsfGVufDB8fHxvcmFuZ2V8MTc4ODg1NDk5NXww&ixlib=rb-4.1.0&q=85",
        "description": "Paper texture for decorative background overlay at 4–6% opacity (never behind text blocks)."
      }
    ]
  },

  "implementation_notes_js": {
    "react_files": "Project uses .js (not .tsx). Keep components in JS, use PropTypes only if already used elsewhere.",
    "i18n": {
      "rule": "Do not hardcode copy in components. Use a simple dictionary map (id/en) and a t(key) helper.",
      "keys_examples": [
        "landing.hero.title",
        "landing.hero.cta",
        "wizard.step.discover",
        "research.findings.label.researchBacked"
      ]
    },
    "testids": {
      "rule": "All interactive + key informational elements must include data-testid in kebab-case.",
      "examples": [
        "data-testid=\"landing-primary-cta-button\"",
        "data-testid=\"wizard-step-item-research\"",
        "data-testid=\"research-sources-table\"",
        "data-testid=\"opportunity-build-button-123\""
      ]
    }
  },

  "instructions_to_main_agent": [
    "Update /frontend/src/index.css :root tokens to match the palette (convert HEX to HSL). Keep backgrounds solid (paper/card).",
    "Remove any centered App header styling from App.css; do not center the entire app container.",
    "Build the landing hero as a left-aligned problem-first message with ONE primary CTA and a right-side ‘factory line’ preview card.",
    "Implement the creation wizard with a sticky vertical stepper on desktop and a horizontal ScrollArea stepper on mobile.",
    "Use shadcn/ui components for all inputs, dialogs, tables, tabs, selects, calendar, etc. No raw HTML dropdowns.",
    "Opportunity cards: implement 6 metric bars + overall score; add sort/filter/compare; compare uses Sheet/Drawer.",
    "Market research: show sources table with clickable URLs and findings labeled RESEARCH-BACKED/HYPOTHESIS/ASSUMPTION.",
    "All interactive and key informational elements must include stable data-testid attributes (kebab-case).",
    "Use Sonner for toasts; show progress + skeletons for long AI steps; always label what’s happening.",
    "Avoid gradients except the hero background accents (max 20% viewport)."
  ],

  "general_ui_ux_design_guidelines": "\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n"
}
