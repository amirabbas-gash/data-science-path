"use client";
export default function ErrorPage({error,reset}:{error:Error,reset:()=>void}){return <div className="card mx-auto mt-20 max-w-xl text-center"><h2 className="text-xl font-bold">Something interrupted this view</h2><p className="mt-2 text-sm text-muted">{error.message}</p><button className="btn-primary mt-5" onClick={reset}>Try again</button></div>}

