export async function api<T>(path:string, init?:RequestInit):Promise<T>{
  const response=await fetch(`/api${path}`,{...init,credentials:"include",headers:{"Content-Type":"application/json",...(init?.headers||{})}});
  if(response.status===401 && typeof window!=="undefined" && !location.pathname.startsWith("/login")){location.href="/login"; throw new Error("Authentication required");}
  if(!response.ok){const body=await response.json().catch(()=>({detail:"Request failed"}));throw new Error(body.detail||"Request failed");}
  return response.status===204 ? (undefined as T) : response.json();
}
export const cx=(...values:(string|false|null|undefined)[])=>values.filter(Boolean).join(" ");

