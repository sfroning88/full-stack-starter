module.exports = async ({ github, context }) => {
  const pr = context.payload.pull_request;
  await github.rest.issues.addAssignees({
    ...context.repo,
    issue_number: context.issue.number,
    assignees: [pr.user.login],
  });
  await github.rest.issues.addLabels({
    ...context.repo,
    issue_number: context.issue.number,
    labels: ["enhancement"],
  });
};
