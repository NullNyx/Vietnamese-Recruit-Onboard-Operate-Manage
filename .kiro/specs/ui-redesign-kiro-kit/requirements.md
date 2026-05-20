# Requirements Document

## Introduction

Redesign the Vroom HR frontend UI following the kiro-kit design philosophy. The current interface uses generic defaults (Inter font, no dark mode, minimal components, no animations) and lacks a distinctive visual identity. This redesign establishes a bold, intentional design system with proper dark mode, motion design, expanded component usage, responsive layouts, and accessibility compliance — while preserving all existing functionality and the Vietnamese-first UI language.

## Glossary

- **Design_System**: The collection of design tokens (colors, typography, spacing, radii), CSS variables, and Tailwind configuration that define the visual language of Vroom HR
- **Theme_Provider**: The next-themes integration that manages light/dark mode switching and persists user preference
- **Sidebar**: The primary navigation component on the left side of the dashboard layout containing links to all application sections
- **Command_Bar**: A keyboard-accessible search/command palette (⌘K) for quick navigation between pages and actions
- **Toast_System**: A notification component that displays transient feedback messages for user actions
- **Form_Engine**: The combination of react-hook-form for state management and zod for schema validation used in all form interfaces
- **Motion_System**: The animation framework using CSS transitions, keyframes, and Tailwind animate utilities for micro-interactions and page transitions
- **Component_Library**: The set of shadcn/ui components installed and configured for use across the application
- **Breakpoint**: Responsive design thresholds — sm (640px), md (768px), lg (1024px), xl (1280px)

## Requirements

### Requirement 1: Design Token System

**User Story:** As a developer, I want a comprehensive design token system with CSS variables for both light and dark themes, so that the entire UI has a cohesive, distinctive visual identity that can be toggled between modes.

#### Acceptance Criteria

1. THE Design_System SHALL define CSS variables in HSL format for all semantic color roles: background, foreground, card, card-foreground, popover, popover-foreground, primary, primary-foreground, secondary, secondary-foreground, muted, muted-foreground, accent, accent-foreground, destructive, destructive-foreground, border, input, ring, sidebar-background, sidebar-foreground, sidebar-border, sidebar-accent, sidebar-accent-foreground, and at least 5 chart color variables (chart-1 through chart-5)
2. THE Design_System SHALL define a dark theme variant with all corresponding CSS variables applied via the `.dark` class selector, where every color role defined in the light theme has a corresponding dark theme value
3. THE Design_System SHALL use a primary color in the teal-to-emerald hue range (HSL hue between 150 and 175 degrees) and accent colors in the warm hue range (HSL hue between 15 and 45 degrees), such that the primary color differs from the shadcn/ui default (HSL 222.2 47.4% 11.2%) by at least 40 degrees of hue
4. THE Design_System SHALL define a spacing scale of at least 4 steps (sm, md, lg, xl) as CSS variables, at least 3 border-radius tokens, and at least 3 shadow elevation tokens (sm, md, lg), all registered in the Tailwind config `theme.extend` so they are consumable as Tailwind utility classes
5. WHEN the application loads, THE Design_System SHALL resolve the theme by checking in this order: (1) user's persisted preference stored in localStorage, (2) the operating system's `prefers-color-scheme` media query value; and apply the `.dark` class to the document root element if the resolved theme is dark
6. IF no persisted theme preference exists in localStorage and the system preference is unavailable, THEN THE Design_System SHALL default to the light theme

### Requirement 2: Typography System

**User Story:** As a user, I want the application to use distinctive, readable typography that feels intentional and professional, so that the interface has visual character beyond generic defaults.

#### Acceptance Criteria

1. THE Design_System SHALL use a display font from the following approved set (Plus Jakarta Sans, Outfit, or Satoshi) for headings (h1–h4) and a separate complementary sans-serif font for body text, with neither font being Inter
2. THE Design_System SHALL load all custom fonts via next/font with subset configuration that includes both "latin" and "latin-ext" subsets to support Vietnamese characters
3. THE Design_System SHALL define a typographic scale specifying font-size, line-height, and letter-spacing for each of the following 7 levels: h1 (36–48px), h2 (28–36px), h3 (22–28px), h4 (18–22px), body (14–16px), small (12–13px), and caption (11–12px)
4. THE Design_System SHALL apply font-smoothing (antialiased) globally for crisp text rendering
5. IF a custom font fails to load, THEN THE Design_System SHALL fall back to a system sans-serif font stack that supports Vietnamese characters without layout shift
6. THE Design_System SHALL expose the heading and body font families as CSS variables or Tailwind theme tokens so that components can reference them consistently across the application

### Requirement 3: Dark Mode Support

**User Story:** As a user, I want to switch between light and dark modes, so that I can use the application comfortably in different lighting conditions.

#### Acceptance Criteria

1. THE Theme_Provider SHALL integrate next-themes with the `attribute="class"` strategy and `defaultTheme="system"`
2. THE Theme_Provider SHALL persist the user's theme choice in localStorage so that the selected theme is restored on subsequent page loads without a visible flash of the incorrect theme
3. WHEN the user clicks the theme toggle, THE Theme_Provider SHALL cycle through themes in the fixed order: light → dark → system → light
4. THE Theme_Provider SHALL render a toggle button in the application header that displays the currently active theme mode (light, dark, or system), is focusable via keyboard Tab navigation, activatable via Enter or Space key, and exposes an accessible label indicating the current theme and the action to switch
5. WHILE the dark theme is active, THE Design_System SHALL apply a complete set of dark color CSS variables (background, foreground, primary, secondary, muted, accent, destructive, border, input, ring) and ensure all text meets WCAG 2.1 AA contrast ratio (4.5:1 for normal text, 3:1 for large text)
6. WHILE the system theme is selected, WHEN the operating system color scheme preference changes, THE Theme_Provider SHALL update the applied theme within 1 second without requiring a page reload

### Requirement 4: Expanded Component Library

**User Story:** As a developer, I want a full set of shadcn/ui components installed and configured, so that I can build consistent, accessible interfaces without custom implementations.

#### Acceptance Criteria

1. THE Component_Library SHALL include the following shadcn/ui components as individual files in the `components/ui` directory: Button, Input, Label, Textarea, Select, Checkbox, Switch, Dialog, Sheet, Dropdown Menu, Navigation Menu, Table, Card, Badge, Avatar, Tooltip, Separator, Skeleton, Tabs, Command, Popover, Calendar, Toast (Sonner), and Form (24 components total)
2. THE Component_Library SHALL configure all components to reference Design_System CSS variables (via Tailwind utility classes mapped to `hsl(var(--*))` tokens) for colors, border-radius, and ring styles, with no hardcoded color values in component source files
3. THE Component_Library SHALL apply focus-visible styles on all interactive components using the classes `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
4. THE Component_Library SHALL maintain Radix UI primitives as the accessibility foundation for all overlay and interactive components, with corresponding `@radix-ui/*` packages listed as dependencies in package.json
5. WHEN all components are installed, THE Component_Library SHALL pass the project build (`next build`) without TypeScript or module resolution errors
6. THE Component_Library SHALL list all required peer dependencies (including `sonner`, `react-hook-form`, `@hookform/resolvers`, `zod`, `cmdk`, `date-fns`, `react-day-picker`) in package.json for the Form, Toast, Command, and Calendar components

### Requirement 5: Application Shell and Navigation

**User Story:** As a user, I want a polished navigation experience with a collapsible sidebar, breadcrumbs, and quick-access command bar, so that I can move efficiently between sections of the application.

#### Acceptance Criteria

1. THE Sidebar SHALL be collapsible between expanded state (showing icon + label, 256px wide) and collapsed state (icon-only, 64px wide) with a CSS transition lasting between 150ms and 300ms
2. THE Sidebar SHALL persist its collapsed/expanded state in localStorage so that the state is restored on page reload; IF localStorage is unavailable, THEN THE Sidebar SHALL default to the expanded state
3. WHEN the viewport width is below 768px (Tailwind md breakpoint), THE Sidebar SHALL render as a Sheet (slide-over drawer) triggered by a hamburger menu button in the application header
4. THE Sidebar SHALL display the Vroom HR logo at the top, navigation links (Dashboard, Employees, Departments, Positions, Gmail) each with an associated icon, and a user section at the bottom containing a logout action
5. THE Sidebar SHALL visually distinguish the currently active navigation link from inactive links using a distinct background or text style
6. WHEN the user presses ⌘K (macOS) or Ctrl+K (Windows/Linux), THE Command_Bar SHALL open a searchable command palette listing all navigation pages (Dashboard, Employees, Departments, Positions, Gmail) and filter results in real time as the user types
7. IF the Command_Bar search query matches no navigation items, THEN THE Command_Bar SHALL display a "No results found" message
8. WHEN the user selects an item in the Command_Bar, THE application SHALL navigate to the corresponding page and close the Command_Bar
9. THE application header SHALL display breadcrumbs reflecting the current route hierarchy (e.g., "Home / Employees" or "Home / Settings / Departments"), where each ancestor segment is a clickable link except the last segment representing the current page

### Requirement 6: Motion and Micro-Interactions

**User Story:** As a user, I want subtle animations and transitions throughout the interface, so that the application feels responsive and polished rather than static.

#### Acceptance Criteria

1. THE Motion_System SHALL apply enter/exit animations to all overlay components (Dialog, Sheet, Dropdown, Popover) using CSS keyframes with a duration between 150ms and 250ms
2. THE Motion_System SHALL apply staggered fade-in animations to list items (table rows, card grids) on initial page load with a per-item delay of 50ms and a maximum of 10 staggered items
3. THE Motion_System SHALL apply smooth transitions (150–300ms, ease-out) to all interactive state changes (hover, focus, active) on buttons, links, form inputs, and card components
4. WHEN a page route changes, THE Motion_System SHALL apply a fade transition with a duration of 200ms and opacity animating from 0 to 1 to the main content area
5. WHEN the user's operating system has `prefers-reduced-motion: reduce` enabled, THE Motion_System SHALL disable all animations and transitions except opacity changes on overlay show/hide
6. THE Motion_System SHALL define reusable Tailwind animation utilities (fade-in, slide-up, slide-in-from-left, scale-in) in the Tailwind configuration

### Requirement 7: Login Page Redesign

**User Story:** As a user, I want the login page to feel distinctive and welcoming with atmospheric design, so that my first impression of the application conveys quality and intentionality.

#### Acceptance Criteria

1. THE Login page SHALL display a full-viewport layout (100vw × 100vh) with a non-solid background that uses at least one decorative technique (gradient mesh, geometric pattern, or noise texture) covering the entire viewport with no visible tiling seams
2. THE Login page SHALL center a login card both horizontally and vertically containing, in order: the Vroom HR logo, application name, tagline, a consent notice, and the Google OAuth button
3. THE Login page SHALL apply a staggered fade-in entrance animation to the login card elements with a total animation duration between 400ms and 1200ms and a per-element stagger delay between 50ms and 150ms
4. IF the user has enabled `prefers-reduced-motion`, THEN THE Login page SHALL disable the staggered entrance animation and display all elements immediately without motion
5. WHILE the dark theme is active, THE Login page SHALL render the background and card using the Design_System dark theme CSS variables, maintaining WCAG 2.1 AA contrast ratio (4.5:1) between card text and card background
6. THE Login page SHALL maintain the existing Google OAuth login flow without functional changes — clicking the Google OAuth button SHALL redirect to `/api/auth/login`

### Requirement 8: Dashboard Page

**User Story:** As a user, I want the dashboard to provide a useful overview with summary cards and quick actions, so that I can see the state of my HR data at a glance.

#### Acceptance Criteria

1. THE Dashboard page SHALL display summary statistic cards showing: total employees, total departments, total positions, and unread emails count, each rendered using the Card component with a corresponding icon indicator from lucide-react
2. THE Dashboard page SHALL display a "Hành động nhanh" (Quick Actions) section containing shortcut buttons to: add a new employee, view the employee list, manage departments, and manage positions
3. WHEN the Dashboard page loads, THE Dashboard page SHALL apply staggered entrance animations to the summary cards with a delay of 100ms between each successive card
4. THE Dashboard page SHALL use a responsive grid layout: 1 column at viewports below 640px, 2 columns at viewports between 640px and 1023px, and 4 columns at viewports 1024px and above
5. IF the Gmail integration is not connected, THEN THE Dashboard page SHALL display the unread emails card with a count of 0 and a visual indicator that Gmail is not linked
6. WHILE summary data is being fetched, THE Dashboard page SHALL display placeholder skeleton cards in place of the statistic values

### Requirement 9: Data Table Pages (Employees, Departments, Positions)

**User Story:** As a user, I want data-heavy pages to use proper table components with sorting, filtering, and pagination UI, so that I can efficiently browse and manage records.

#### Acceptance Criteria

1. THE data table pages SHALL use the shadcn/ui Table component with thead containing column headers, tbody containing data rows, and tfoot containing pagination summary
2. THE data table pages SHALL display a toolbar containing a search text input (maximum 100 characters), entity-specific filter dropdowns (department, position, and active status for Employees), and action buttons (Add, Import)
3. THE data table pages SHALL display pagination controls showing current page number, total pages, and a page size selector with options of 10, 20, 50, or 100 items per page (default: 20)
4. WHILE data is being fetched from the API, THE data table pages SHALL display Skeleton components in place of table rows, rendering at least 5 placeholder rows matching the table column layout
5. WHEN a table row is clicked, THE data table page SHALL navigate to the detail view for that record
6. WHEN the viewport width is below 768px (Tailwind md breakpoint), THE data table pages SHALL switch from the table layout to a card-based layout displaying one card per record
7. IF the API returns an error or the data set is empty, THEN THE data table pages SHALL display a centered message indicating the condition (error description or "no records found") in place of the table body
8. WHEN the user types in the search input, THE data table pages SHALL debounce the input by 300ms before sending the filtered request to the API

### Requirement 10: Form Patterns and Validation

**User Story:** As a user, I want forms to provide clear validation feedback with inline error messages, so that I can correct mistakes without confusion.

#### Acceptance Criteria

1. THE Form_Engine SHALL use react-hook-form with zod schema validation for all form interfaces (employee creation, department creation, position creation)
2. WHEN the user submits a form or moves focus away from a required field that fails zod schema validation, THE Form_Engine SHALL display an inline error message below the corresponding input field using the destructive color token within 200 milliseconds
3. WHILE the form is submitting, THE Form_Engine SHALL disable the submit button and display a loading spinner inside the submit button
4. IF a form submission fails due to a server error, THEN THE Toast_System SHALL display an error notification containing the server-provided error message, and THE Form_Engine SHALL preserve all user-entered form data so the user can correct and resubmit without re-entering values
5. IF a form submission fails due to a server error and the server response contains no error message, THEN THE Toast_System SHALL display a generic error notification indicating the submission failed
6. WHEN a form submission succeeds, THE Toast_System SHALL display a success notification and navigate to the corresponding list view (employees list for employee forms, departments list for department forms, positions list for position forms)
7. THE Form_Engine SHALL use the shadcn/ui Form component wrapper for consistent label, description, and error message layout

### Requirement 11: Toast and Notification System

**User Story:** As a user, I want transient feedback notifications for my actions, so that I know whether operations succeeded or failed without blocking my workflow.

#### Acceptance Criteria

1. THE Toast_System SHALL use Sonner (shadcn/ui toast integration) for all transient notifications
2. THE Toast_System SHALL support success, error, warning, and info variants, each rendered with a visually distinct color using Design_System color tokens and accompanied by a variant-identifying icon
3. THE Toast_System SHALL position toasts in the bottom-right corner with stacked display, showing a maximum of 5 toasts simultaneously and removing the oldest toast when the limit is exceeded
4. THE Toast_System SHALL auto-dismiss success and info toasts after 4 seconds, auto-dismiss warning toasts after 6 seconds, and persist error toasts until the user dismisses them via a visible close button
5. THE Toast_System SHALL be accessible — success, warning, and info toasts render in an aria-live="polite" region, error toasts render in an aria-live="assertive" region, and each toast includes a role="status" or role="alert" attribute respectively

### Requirement 12: Responsive Design

**User Story:** As a user, I want the application to be fully usable on mobile devices and tablets, so that I can manage HR tasks from any device.

#### Acceptance Criteria

1. THE application layout SHALL render all page content within the viewport width without requiring horizontal scrolling on any screen width from 320px upward, and SHALL apply base styles for mobile viewports first with progressive enhancements at larger breakpoints using Tailwind breakpoint utilities (sm: 640px, md: 768px, lg: 1024px)
2. WHILE the viewport width is below 768px (md breakpoint), THE Sidebar SHALL be hidden from the default layout and replaced by a hamburger menu button in the header that opens the navigation as a Sheet drawer overlay, and WHEN the user taps a navigation link or taps outside the Sheet or taps a close button, THE Sheet drawer SHALL close
3. WHILE the viewport width is below 640px (sm breakpoint), THE data tables SHALL transform into a vertically stacked card layout where each row is displayed as an individual card with labeled field-value pairs, preserving all visible data from the table row
4. WHILE the viewport width is below 768px (md breakpoint), THE application SHALL ensure all interactive elements (buttons, links, menu items) have a minimum touch target size of 44x44 CSS pixels
5. WHEN the viewport is resized or the device orientation changes, THE application layout SHALL adapt to the new viewport width without requiring a page reload and without content overflow causing horizontal scrolling

### Requirement 13: Accessibility Compliance

**User Story:** As a user with assistive technology, I want the application to be navigable and operable with keyboard and screen readers, so that I can use all features without barriers.

#### Acceptance Criteria

1. THE application SHALL ensure all interactive elements are reachable via keyboard Tab navigation following the visual layout order (left-to-right, top-to-bottom within each landmark region)
2. THE application SHALL provide visible focus indicators with a minimum 2px outline offset on all focusable elements, using the ring color defined in the design system
3. THE application SHALL use semantic HTML landmarks (header, nav, main, aside) for screen reader navigation, with each landmark appearing at most once per page or distinguished by an aria-label when repeated
4. THE application SHALL ensure all images have alt text describing their content, and all decorative icons have aria-hidden="true" while actionable icons have an aria-label describing their action
5. THE application SHALL ensure color is not the sole means of conveying information (icons, text labels, or patterns accompany color indicators)
6. THE application SHALL meet WCAG 2.1 AA contrast ratios (minimum 4.5:1 for normal text, 3:1 for large text and interactive element boundaries) for all text and interactive elements
7. WHEN a modal dialog or popover opens, THE application SHALL move keyboard focus to the first focusable element within it, trap Tab cycling within it, and return focus to the triggering element when it closes
8. THE application SHALL ensure all form inputs have a programmatically associated label element or aria-label, and validation error messages are linked to their respective input via aria-describedby
9. WHEN dynamic content updates occur (toast notifications, loading states, inline errors), THE application SHALL announce changes to screen readers using an aria-live region with appropriate politeness level (polite for non-urgent, assertive for errors)

### Requirement 14: Vietnamese-First UI Language

**User Story:** As a Vietnamese HR user, I want all interface labels, navigation items, and system messages in Vietnamese, so that the application feels native to my workflow.

#### Acceptance Criteria

1. THE application SHALL display all navigation labels, page titles, button text, form labels, placeholder text, and system-generated messages in Vietnamese, except for proper nouns and brand names (e.g., "Vroom HR", "Gmail", "Google") which SHALL remain in their original form
2. THE application SHALL set the HTML lang attribute to "vi"
3. THE application SHALL format dates using Vietnamese locale (dd/MM/yyyy), numbers using dot as thousands separator and comma as decimal separator, and currency values in VND format (e.g., "1.000.000 ₫")
4. IF a system message or error is returned from the backend without a Vietnamese translation, THEN THE application SHALL display it with a Vietnamese contextual prefix label indicating the message type (e.g., "Lỗi:" for errors, "Thông báo:" for informational messages) followed by the original message text
5. WHEN the application renders any page, THE application SHALL not display any English-language UI text in navigation items, button labels, form labels, table headers, or status messages, excluding brand names and technical identifiers
