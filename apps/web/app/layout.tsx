import type {Metadata} from "next";import "./globals.css";import {Shell} from "@/components/shell";
export const metadata:Metadata={title:"Data Science Path",description:"Adaptive learning for applied data science"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><body><Shell>{children}</Shell></body></html>}

