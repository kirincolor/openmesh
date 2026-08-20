# Local files

Use this skill when the human wants files, a project, or an office document on this computer.

1. Call `pc_list` on `.` (and `recursive` if needed) to see the allowed folders.
2. Source code is a real file with the right suffix: `main.cpp`, `App.java`, `app.py`. Never put a program in a `.md` file.
3. A project is a folder: create it, then `pc_write` every file (source, headers, build files). Add `README.md` only as a real readme beside the code.
4. Word / Excel / PowerPoint: `office_write` to `reports/name.docx` (or `.xlsx` / `.pptx`).
5. `doc_write` only attaches one downloadable file to the chat. Prefer disk for anything the human will keep.
6. Stay inside allowed computer folders or your workspace.
