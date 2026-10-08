const VERCEL_BOT_LOGIN = "vercel[bot]";
const MAX_TIMEOUT_MS = 5 * 60 * 1000;
const POLL_INTERVAL_MS = 10 * 1000;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const findVercelDeployment = async ({ github, owner, repo, sha }) => {
  const { data } = await github.rest.repos.listDeployments({
    owner,
    repo,
    sha,
    per_page: 100,
  });
  return data.find((d) => d.creator?.login === VERCEL_BOT_LOGIN) ?? null;
};

const findSuccessStatus = async ({ github, owner, repo, deploymentId }) => {
  const { data } = await github.rest.repos.listDeploymentStatuses({
    owner,
    repo,
    deployment_id: deploymentId,
    per_page: 100,
  });
  return data.find((s) => s.state === "success") ?? null;
};

const probeWithBypass = async ({ targetUrl, bypassSecret }) => {
  const probeUrl = new URL(targetUrl);
  probeUrl.searchParams.set("x-vercel-protection-bypass", bypassSecret);
  probeUrl.searchParams.set("x-vercel-set-bypass-cookie", "true");

  const response = await fetch(probeUrl.toString(), {
    redirect: "follow",
    headers: { "x-vercel-protection-bypass": bypassSecret },
  });
  return response.status;
};

module.exports = async ({ github, context, core }) => {
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;
  if (!bypassSecret) {
    core.setFailed("VERCEL_AUTOMATION_BYPASS_SECRET is not set");
    return;
  }

  const { owner, repo } = context.repo;
  const sha = context.payload.pull_request?.head?.sha ?? context.sha;
  if (!sha) {
    core.setFailed("Unable to determine commit SHA");
    return;
  }

  core.info(`Looking for ${VERCEL_BOT_LOGIN} deployment on ${sha}`);

  const deadline = Date.now() + MAX_TIMEOUT_MS;
  let deployment = null;
  while (Date.now() < deadline) {
    deployment = await findVercelDeployment({ github, owner, repo, sha });
    if (deployment) break;
    core.info(`No ${VERCEL_BOT_LOGIN} deployment yet, retrying...`);
    await wait(POLL_INTERVAL_MS);
  }
  if (!deployment) {
    core.setFailed(`Timed out waiting for ${VERCEL_BOT_LOGIN} deployment`);
    return;
  }

  core.info(`Found deployment ${deployment.id}, waiting for success status`);

  let status = null;
  while (Date.now() < deadline) {
    status = await findSuccessStatus({
      github,
      owner,
      repo,
      deploymentId: deployment.id,
    });
    if (status) break;
    core.info("Deployment status not yet success, retrying...");
    await wait(POLL_INTERVAL_MS);
  }
  if (!status?.target_url) {
    core.setFailed("Timed out waiting for deployment success status");
    return;
  }

  const targetUrl = status.target_url;
  core.info(`target url » ${targetUrl}`);

  while (Date.now() < deadline) {
    try {
      const code = await probeWithBypass({ targetUrl, bypassSecret });
      core.info(`Probe responded ${code}`);
      if (code >= 200 && code < 400) {
        core.setOutput("url", targetUrl);
        return;
      }
    } catch (error) {
      core.info(`Probe error: ${error.message}`);
    }
    await wait(POLL_INTERVAL_MS);
  }

  core.setFailed(`Timed out waiting for 2xx/3xx from ${targetUrl}`);
};
