import type { ChangeEvent } from "react";

export const iconClass = "h-4 w-4 md:h-[18px] md:w-[18px]";

export const btnClass = `
  inline-flex items-center justify-center rounded-md border border-white font-semibold transition-colors p-1.5 md:p-2
  bg-white/4 text-white hover:bg-white/12
  disabled:opacity-40 disabled:pointer-events-none
`;

export const selectClass = `
    rounded-md border border-white/20 bg-surface-dark font-data text-white/80
`;

export function onSelectChange<T extends string>(onChange: (value: T) => void) {
  return (event: ChangeEvent<HTMLSelectElement>) => {
    onChange((event.target as unknown as { value: string }).value as T);
  };
}
