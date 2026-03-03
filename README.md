# Running LancasterLink Locally

**Follow these steps to run the project on your machine**

1. Install Node.js
    - Make sure you have **Node.js** installed.
    - Download from: https://nodejs.org/
2. Navigate to the Frontend Folder
    - in a terminal, run: `cd frontend`
    - so you should be in `LancasterLink\frontend>`
3. Install Dependencies
    - If this is your first time running it then, in the same terminal run: `npm install`
    - You only need to do this when:
        - The `package.json` file changes
        - The `node_modules` folder is deleted
4. Start the Development Server
    - Run: `npm run dev`
    - You should see something like: `Local: http://localhost:3000`
    - Open that link in your browser.


# Running All Tests

**Running all tests before pushing**
Run the full collection of Python tests from the workspace root:
```bash
python -m pytest tests -v
```
This covers every unit and integration test under `tests/` with verbose output.


# Issues With the Project

Any issues with the project please raise in the **Issues** tab at the top of the github.

# Running The Project

Anything that needs to be done to either run or test the project please put in the **readme.md**
