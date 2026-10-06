import { request } from "./client";

export async function fetchPanel(token) {
  return request("/panel", { token });
}
