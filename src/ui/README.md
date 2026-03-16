# Skill Scope UI

This directory contains the Electron + React frontend for Skill Scope.

## Prerequisites

*   **Node.js**: Ensure you have Node.js installed (LTS version recommended).

## Installation

1.  Open your terminal in the repository root.
2.  Navigate to the UI folder:
    ```bash
    cd src/ui
    ```
3.  Install the dependencies:
    ```bash
    npm install
    ```

## Running in Development

To start the app with hot-reloading (changes to code update the window instantly):
```bash
npm run dev
```

## Building the Executable

To package the application into a standalone Windows `.exe` file:
```bash
npm run dist
```

The installer will be generated in the `src/ui/release/` folder.
