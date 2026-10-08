const fs = require("fs");

module.exports = async ({ github, context }) => {
  const resultsPath = "/tmp/playwright-results.txt";
  if (!fs.existsSync(resultsPath)) return;

  const raw = fs.readFileSync(resultsPath, "utf8").trim();
  if (!raw) return;

  const marker = "<!-- playwright-smoke -->";
  const body = `${marker}\n## Playwright Smoke Tests\n\n\`\`\`\n${raw}\n\`\`\``;

  const comments = await github.paginate(github.rest.issues.listComments, {
    ...context.repo,
    issue_number: context.issue.number,
    per_page: 100,
  });

  const prev = comments.filter((c) => c.body?.startsWith(marker));
  await Promise.allSettled(
    prev.map((c) =>
      github.rest.issues.deleteComment({
        ...context.repo,
        comment_id: c.id,
      }),
    ),
  );

  await github.rest.issues.createComment({
    ...context.repo,
    issue_number: context.issue.number,
    body,
  });
};
