import { nanoid } from "nanoid";

/** Generate a unique ID for database records */
export function generateId(prefix?: string): string {
  const id = nanoid(16);
  return prefix ? `${prefix}_${id}` : id;
}
