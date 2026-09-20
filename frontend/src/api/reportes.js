import { request } from "./client";

export async function fetchReportes(token) {
  return request("/reportes", { token });
}
