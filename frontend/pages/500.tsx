import Link from 'next/link';
import Head from 'next/head';

export default function Custom500() {
  return (
    <>
      <Head>
        <title>500 - Error del Servidor | Alex Asesor Financiero IA</title>
      </Head>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-red-500 mb-4">500</h1>
          <h2 className="text-2xl font-semibold text-dark mb-4">Error Interno del Servidor</h2>
          <p className="text-gray-600 mb-8">
            Algo salió mal en nuestro lado. Por favor, inténtalo de nuevo más tarde.
          </p>
          <Link href="/dashboard">
            <button className="bg-primary hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors">
              Volver al Panel de Control
            </button>
          </Link>
        </div>
      </div>
    </>
  );
}