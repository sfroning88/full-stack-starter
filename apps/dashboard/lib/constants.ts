export const PROVIDER_STALE_TIME = 60 * 1000;

export const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export const USER_ID_COOKIE_NAME = "fiery-spirit-user-id";

export const COOKIE_BANNER_DISMISSED_KEY =
  "fiery-spirit-cookie-banner-dismissed";

export const COOKIE_BANNER_SYNC_EVENT = `${COOKIE_BANNER_DISMISSED_KEY}:sync`;

export const COOKIE_BANNER_MESSAGE =
  "This site uses one first-party cookie for anonymous analytics. No third-party tracking.";

export const QUERY_STALE_TIME = 60 * 60 * 5;

export const CACHE_STALE_TIME = 60 * 60 * 60;

export const PRIVACY_DOC_PATH = "lib/docs/repo/PRIVACY.md";

export const MOBILE_BREAKPOINT = 768;

export const IMAGE_LOADING = "/sprites/loading.jpeg";

export const VOLCANO_SPRITE = "/sprites/volcano.png";

export const EMPTY_VOLCANOES: readonly [] = Object.freeze([]);

export const EMPTY_MODELS: readonly [] = Object.freeze([]);
