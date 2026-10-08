export const QUERY_KEYS = {
  user: (userId: string) => ["user", userId] as const,
  messages: (userId: string) => ["myClasses", userId] as const,
};
