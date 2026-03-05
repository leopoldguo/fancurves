
# AGENTS

<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: `npx openskills read <skill-name>` (run in your shell)
  - For multiple: `npx openskills read skill-one,skill-two`
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

<skill>
<name>brainstorming</name>
<description>"You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."</description>
<location>global</location>
</skill>

<skill>
<name>canvas-design</name>
<description>"Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create ..."</description>
<location>global</location>
</skill>

<skill>
<name>context-compression</name>
<description>"Design and evaluate compression strategies for long-running sessions"</description>
<location>global</location>
</skill>

<skill>
<name>context-degradation</name>
<description>"Recognize patterns of context failure: lost-in-middle, poisoning, distraction, and clash"</description>
<location>global</location>
</skill>

<skill>
<name>context-fundamentals</name>
<description>"Understand what context is, why it matters, and the anatomy of context in agent systems"</description>
<location>global</location>
</skill>

<skill>
<name>context-optimization</name>
<description>"Apply compaction, masking, and caching strategies"</description>
<location>global</location>
</skill>

<skill>
<name>dispatching-parallel-agents</name>
<description>Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies</description>
<location>global</location>
</skill>

<skill>
<name>doc-coauthoring</name>
<description>"Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This ..."</description>
<location>global</location>
</skill>

<skill>
<name>evaluation</name>
<description>"Build evaluation frameworks for agent systems"</description>
<location>global</location>
</skill>

<skill>
<name>executing-plans</name>
<description>Use when you have a written implementation plan to execute in a separate session with review checkpoints</description>
<location>global</location>
</skill>

<skill>
<name>finishing-a-development-branch</name>
<description>Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup</description>
<location>global</location>
</skill>

<skill>
<name>frontend-design</name>
<description>"Create distinctive, production-grade frontend interfaces with intentional aesthetics, high craft, and non-generic visual identity. Use when building or styling web UIs, components, pages, dashboard..."</description>
<location>global</location>
</skill>

<skill>
<name>mcp-builder</name>
<description>"Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate exte..."</description>
<location>global</location>
</skill>

<skill>
<name>memory-systems</name>
<description>"Design short-term, long-term, and graph-based memory architectures"</description>
<location>global</location>
</skill>

<skill>
<name>multi-agent-patterns</name>
<description>"Master orchestrator, peer-to-peer, and hierarchical multi-agent architectures"</description>
<location>global</location>
</skill>

<skill>
<name>notebooklm</name>
<description>"Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Browser automation, library management, persistent auth...."</description>
<location>global</location>
</skill>

<skill>
<name>planning-with-files</name>
<description>"Implements Manus-style file-based planning for complex tasks. Creates task_plan.md, findings.md, and progress.md. Use when starting complex multi-step tasks, research projects, or any task requirin..."</description>
<location>global</location>
</skill>

<skill>
<name>react-best-practices</name>
<description>"React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance pat..."</description>
<location>global</location>
</skill>

<skill>
<name>receiving-code-review</name>
<description>Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation</description>
<location>global</location>
</skill>

<skill>
<name>requesting-code-review</name>
<description>Use when completing tasks, implementing major features, or before merging to verify work meets requirements</description>
<location>global</location>
</skill>

<skill>
<name>skill-creator</name>
<description>"This skill should be used when the user asks to create a new skill, build a skill, make a custom skill, develop a CLI skill, or wants to extend the CLI with new capabilities. Automates the entire s..."</description>
<location>global</location>
</skill>

<skill>
<name>slack-gif-creator</name>
<description>"Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. Use when users request animated GIFs for Slack like \"..."</description>
<location>global</location>
</skill>

<skill>
<name>subagent-driven-development</name>
<description>Use when executing implementation plans with independent tasks in the current session</description>
<location>global</location>
</skill>

<skill>
<name>systematic-debugging</name>
<description>Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes</description>
<location>global</location>
</skill>

<skill>
<name>test-driven-development</name>
<description>Use when implementing any feature or bugfix, before writing implementation code</description>
<location>global</location>
</skill>

<skill>
<name>theme-factory</name>
<description>"Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifac..."</description>
<location>global</location>
</skill>

<skill>
<name>tool-design</name>
<description>"Build tools that agents can use effectively, including architectural reduction patterns"</description>
<location>global</location>
</skill>

<skill>
<name>ui-ux-pro-max</name>
<description>"UI/UX design intelligence. 50 styles, 21 palettes, 50 font pairings, 20 charts, 9 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui). Actions: plan, build, cr..."</description>
<location>global</location>
</skill>

<skill>
<name>using-git-worktrees</name>
<description>Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification</description>
<location>global</location>
</skill>

<skill>
<name>using-superpowers</name>
<description>Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions</description>
<location>global</location>
</skill>

<skill>
<name>verification-before-completion</name>
<description>Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always</description>
<location>global</location>
</skill>

<skill>
<name>web-artifacts-builder</name>
<description>"Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state ma..."</description>
<location>global</location>
</skill>

<skill>
<name>web-design-guidelines</name>
<description>"Review UI code for Web Interface Guidelines compliance. Use when asked to \\\"review my UI\\\", \\\"check accessibility\\\", \\\"audit design\\\", \\\"review UX\\\", or \\\"check my site aga..."</description>
<location>global</location>
</skill>

<skill>
<name>webapp-testing</name>
<description>"Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browse..."</description>
<location>global</location>
</skill>

<skill>
<name>writing-plans</name>
<description>Use when you have a spec or requirements for a multi-step task, before touching code</description>
<location>global</location>
</skill>

<skill>
<name>writing-skills</name>
<description>Use when creating new skills, editing existing skills, or verifying skills work before deployment</description>
<location>global</location>
</skill>

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>
