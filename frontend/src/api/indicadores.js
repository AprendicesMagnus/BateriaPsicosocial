import { request } from "./client";

export async function fetchIndicadores(token, organizacionId = null) {
  const path = organizacionId ? `/indicadores?organizacion_id=${organizacionId}` : "/indicadores";
  return request(path, { token });
}
