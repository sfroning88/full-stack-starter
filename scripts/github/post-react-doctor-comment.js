const fs = require("fs");
const { execSync } = require("child_process");

module.exports = async ({ github, context }) => {
  const outputPath = "/tmp/react-doctor-output.txt";
  if (!fs.existsSync(outputPath)) return;

  const raw = fs.readFileSync(outputPath, "utf8").trim();
  if (!raw) return;

  let filtered;
  try {
    filtered = execSync(
      `sh scripts/filter-react-doctor-output.sh "${outputPath}"`,
      { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 },
    ).trim();
  } catch (e) {
    console.error("Filter script failed:", e.message);
    return;
  }
  if (!filtered) return;

  const marker = "<!-- react-doctor -->";
  const body = `${marker}\n## 🩺 React Doctor\n\n\`\`\`\n${filtered}\n\`\`\``;

  const { data: comments } = await github.rest.issues.listComments({
    ...context.repo,
    issue_number: context.issue.number,
  });

  const prev = comments.find((c) => c.body?.startsWith(marker));
  if (prev) {
    await github.rest.issues.deleteComment({
      ...context.repo,
      comment_id: prev.id,
    });
  }

  await github.rest.issues.createComment({
    ...context.repo,
    issue_number: context.issue.number,
    body,
  });
};
