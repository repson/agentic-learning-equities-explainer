import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { ClerkProvider } from "@clerk/nextjs";
import { ToastContainer } from "@/components/Toast";
import ErrorBoundary from "@/components/ErrorBoundary";

// Este archivo inicializa la aplicación principal de Next.js.
// Los textos mostrados al usuario serán traducidos en los componentes correspondientes.

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <ClerkProvider {...pageProps}>
        <Component {...pageProps} />
        <ToastContainer />
      </ClerkProvider>
    </ErrorBoundary>
  );
}
