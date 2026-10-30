"use strict";

const snapshot = JSON.parse(document.getElementById("report-data").textContent);
const labels = {
  identical: "Identical",
  rewritten: "Mechanical rewrites only",
  different: "Remaining differences",
  "missing-local": "Missing locally",
  "local-only": "Local only",
};
let selected = snapshot.files.find((entry) => entry.status === "different") || snapshot.files[0];
let mode = "raw";

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function sourceCells(row, line, number, kind) {
  row.append(element("td", "line-number " + kind, number === null ? "" : String(number)));
  const cell = element("td", "source " + (line === null ? "empty" : kind));
  if (line !== null) {
    cell.append(element("span", "marker", kind === "added" ? "+" : kind === "removed" ? "−" : " "));
    cell.append(document.createTextNode(line.replace(/\r?\n$/, "")));
    if (!line.endsWith("\n")) cell.append(element("span", "eof", "No newline at end of file"));
  }
  row.append(cell);
}

function lineRow(view, leftIndex, rightIndex, kind) {
  const row = element("tr");
  sourceCells(row, leftIndex === null ? null : view.left[leftIndex], leftIndex === null ? null : leftIndex + 1,
    kind === "equal" ? "" : "removed");
  sourceCells(row, rightIndex === null ? null : view.right[rightIndex], rightIndex === null ? null : rightIndex + 1,
    kind === "equal" ? "" : "added");
  return row;
}

function appendEqual(body, view, leftStart, rightStart, count) {
  for (let offset = 0; offset < count; offset += 1) {
    body.append(lineRow(view, leftStart + offset, rightStart + offset, "equal"));
  }
}

function appendBlock(body, view, block) {
  const [kind, leftStart, leftEnd, rightStart, rightEnd] = block;
  const count = Math.max(leftEnd - leftStart, rightEnd - rightStart);
  if (kind === "equal" && count > 10 && document.getElementById("changes-only").checked) {
    appendEqual(body, view, leftStart, rightStart, 3);
    const fold = element("tr", "fold");
    const cell = element("td");
    cell.colSpan = 4;
    const button = element("button", "", "Show " + (count - 6) + " unchanged lines");
    button.type = "button";
    button.addEventListener("click", () => {
      const fragment = document.createDocumentFragment();
      appendEqual(fragment, view, leftStart + 3, rightStart + 3, count - 6);
      fold.replaceWith(fragment);
    });
    cell.append(button);
    fold.append(cell);
    body.append(fold);
    appendEqual(body, view, leftEnd - 3, rightEnd - 3, 3);
    return;
  }
  for (let offset = 0; offset < count; offset += 1) {
    body.append(lineRow(view, leftStart + offset < leftEnd ? leftStart + offset : null,
      rightStart + offset < rightEnd ? rightStart + offset : null, kind));
  }
}

function renderFile() {
  const container = document.getElementById("diff");
  container.replaceChildren();
  document.getElementById("file-name").textContent = selected ? selected.path : "No matching files";
  document.getElementById("file-status").textContent = selected ? labels[selected.status] : "";
  const hashes = document.getElementById("hash-values");
  hashes.replaceChildren();
  document.getElementById("raw").setAttribute("aria-pressed", String(mode === "raw"));
  document.getElementById("normalized").setAttribute("aria-pressed", String(mode === "normalized"));
  document.getElementById("view-note").textContent = mode === "raw"
    ? "Original source text. Left: pinned or explicitly selected pstack snapshot. Right: captured local dstack files."
    : "Existing mechanical rewrites applied to both sides. Line numbers refer to normalized text. A match is not behavior proof.";
  if (!selected) {
    container.append(element("p", "empty-state", "Change the search or status filter to find a file."));
    return;
  }
  for (const [name, value] of [
    ["pstack path", selected.upstream_path || "No upstream counterpart"],
    ["dstack path", selected.path],
    ["pstack SHA-256", selected.upstream_sha256 || "Missing"],
    ["dstack SHA-256", selected.dstack_sha256 || "Missing"],
  ]) {
    hashes.append(element("dt", "", name), element("dd", "", value));
  }
  if (selected.binary) {
    container.append(element("p", "empty-state", "Binary content is not rendered as text. Compare the captured SHA-256 hashes below."));
    return;
  }
  const storedView = selected[mode];
  const view = {
    left: storedView.left === null ? [] : snapshot.sources[storedView.left],
    right: storedView.right === null ? [] : snapshot.sources[storedView.right],
    blocks: storedView.blocks,
  };
  if (!view.blocks.length) {
    container.append(element("p", "empty-state", "No text lines in this comparison. Check the paths and hashes for empty or missing files."));
    return;
  }
  const table = element("table", "diff-table");
  table.setAttribute("aria-label", "pstack and dstack side-by-side source");
  const columns = element("colgroup");
  for (const className of ["number-column", "", "number-column", ""]) columns.append(element("col", className));
  const head = element("thead");
  const heading = element("tr");
  for (const name of ["pstack", "dstack"]) {
    const cell = element("th", "", name);
    cell.colSpan = 2;
    cell.scope = "colgroup";
    heading.append(cell);
  }
  head.append(heading);
  const body = element("tbody");
  for (const block of view.blocks) appendBlock(body, view, block);
  table.append(columns, head, body);
  container.append(table);
  container.scrollTop = 0;
}

function renderNavigation() {
  const query = document.getElementById("search").value.toLowerCase().trim();
  const status = document.getElementById("status").value;
  const files = snapshot.files.filter((entry) => entry.path.toLowerCase().includes(query)
    && (status === "all" || entry.status === status));
  if (!files.includes(selected)) selected = files.find((entry) => entry.status === "different") || files[0];
  const list = document.getElementById("file-list");
  list.replaceChildren();
  const groups = new Map();
  for (const entry of files) {
    const skill = entry.path.split("/")[1];
    if (!groups.has(skill)) {
      const group = element("details", "skill-group");
      group.open = true;
      group.append(element("summary", "", skill));
      groups.set(skill, group);
      list.append(group);
    }
    const button = element("button", "file-button");
    button.type = "button";
    button.setAttribute("aria-pressed", String(entry === selected));
    button.append(element("span", "", entry.path.split("/").slice(2).join("/")), element("span", "badge", labels[entry.status]));
    button.addEventListener("click", () => {
      selected = entry;
      for (const peer of list.querySelectorAll("button")) peer.setAttribute("aria-pressed", String(peer === button));
      renderFile();
    });
    groups.get(skill).append(button);
  }
  document.getElementById("file-count").textContent = files.length + " of " + snapshot.files.length + " files";
  renderFile();
}

function fillScope(id, entries) {
  const list = document.getElementById(id);
  if (!entries.length) list.append(element("li", "", "None."));
  for (const [path, reason] of entries) {
    const item = element("li");
    item.append(element("code", "", path));
    if (reason) item.append(element("span", "", reason));
    list.append(item);
  }
}

fillScope("excluded-skills", snapshot.excluded.filter(([path]) => path.split("/").length === 2));
fillScope("excluded-playbooks", snapshot.excluded.filter(([path]) => path.includes("/playbooks/")));
fillScope("excluded-files", snapshot.excluded.filter(([path]) => path.split("/").length > 2 && !path.includes("/playbooks/")));
fillScope("not-imported", snapshot.not_imported.map((path) => [path, "Owner decision needed before import."]));
fillScope("owned", snapshot.owned.map((path) => [path, ""]));

document.getElementById("search").addEventListener("input", renderNavigation);
document.getElementById("status").addEventListener("change", renderNavigation);
document.getElementById("changes-only").addEventListener("change", renderFile);
for (const view of ["raw", "normalized"]) {
  document.getElementById(view).addEventListener("click", () => {
    mode = view;
    renderFile();
  });
}
for (const section of ["compare", "scope"]) {
  document.getElementById(section + "-tab").addEventListener("click", () => {
    document.getElementById("comparison").hidden = section !== "compare";
    document.getElementById("scope").hidden = section !== "scope";
    document.getElementById("compare-tab").setAttribute("aria-pressed", String(section === "compare"));
    document.getElementById("scope-tab").setAttribute("aria-pressed", String(section === "scope"));
  });
}
renderNavigation();
