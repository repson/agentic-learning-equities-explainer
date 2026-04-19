import Link from 'next/link';
import Head from 'next/head';

export default function Custom404() {
  return (
    <>
      <Head>
        <title>404 - Página no encontrada | Alex Asesor Financiero IA</title>
      </Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-primary mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-dark mb-4">Página no encontrada</h2>
          <p className="text-gray-600 mb-8">
            La página que buscas no existe o ha sido movida.
          </p>
          <Link href="/dashboard">
            <button className="bg-primary hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors">
              Volver al panel
            </button>
          </Link>
        </div>
      </div>
    </>
  );
}