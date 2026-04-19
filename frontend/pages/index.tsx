import { SignInButton, SignUpButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import Head from "next/head";

export default function Home() {
  return (
    <>
      <Head>
        <title>Alex AI Financial Advisor - Gestión de Portafolios Inteligente</title>
      </Head>
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-50">
      {/* Navegación */}
      <nav className="px-8 py-6 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="text-2xl font-bold text-dark">
            Alex <span className="text-primary">AI Financial Advisor</span>
          </div>
          <div className="flex gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-6 py-2 text-primary border border-primary rounded-lg hover:bg-primary hover:text-white transition-colors">
                  Iniciar sesión
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors">
                  Comenzar
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <div className="flex items-center gap-4">
                <Link href="/dashboard">
                  <button className="px-6 py-2 bg-ai-accent text-white rounded-lg hover:bg-purple-700 transition-colors">
                    Ir al Panel
                  </button>
                </Link>
                <UserButton afterSignOutUrl="/" />
              </div>
            </SignedIn>
          </div>
        </div>
      </nav>

      {/* Sección principal */}
      <section className="px-8 py-20">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-dark mb-6">
            Tu Futuro Financiero Potenciado por IA
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Experimenta el poder de agentes autónomos de IA trabajando juntos para analizar tu portafolio,
            planificar tu jubilación y optimizar tus inversiones.
          </p>
          <div className="flex gap-6 justify-center">
            <SignedOut>
              <SignUpButton mode="modal">
                <button className="px-8 py-4 bg-ai-accent text-white text-lg rounded-lg hover:bg-purple-700 transition-colors shadow-lg">
                  Iniciar tu análisis
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard">
                <button className="px-8 py-4 bg-ai-accent text-white text-lg rounded-lg hover:bg-purple-700 transition-colors shadow-lg">
                  Abrir Panel
                </button>
              </Link>
            </SignedIn>
            <button className="px-8 py-4 border-2 border-primary text-primary text-lg rounded-lg hover:bg-primary hover:text-white transition-colors">
              Ver Demostración
            </button>
          </div>
        </div>
      </section>

      {/* Sección de características */}
      <section className="px-8 py-20 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-dark mb-12">
            Conoce a tu equipo asesor de IA
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center p-6 rounded-xl hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-ai-accent mb-2">Planificador Financiero</h3>
              <p className="text-gray-600">Coordina tu análisis financiero completo con una orquestación inteligente</p>
            </div>
            <div className="text-center p-6 rounded-xl hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-primary mb-2">Analista de Portafolio</h3>
              <p className="text-gray-600">Análisis profundo de tus posiciones, métricas de rendimiento y evaluación de riesgo</p>
            </div>
            <div className="text-center p-6 rounded-xl hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-4">📈</div>
              <h3 className="text-xl font-semibold text-success mb-2">Especialista en Gráficas</h3>
              <p className="text-gray-600">Visualiza la composición de tu portafolio con gráficos interactivos</p>
            </div>
            <div className="text-center p-6 rounded-xl hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-accent mb-2">Planificador de Jubilación</h3>
              <p className="text-gray-600">Proyecta tu preparación para la jubilación con simulaciones Monte Carlo</p>
            </div>
          </div>
        </div>
      </section>

      {/* Sección de beneficios */}
      <section className="px-8 py-20 bg-gradient-to-r from-primary/10 to-ai-accent/10">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-dark mb-12">
            Asesoría de IA de Nivel Empresarial
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl shadow-md">
              <div className="text-accent text-2xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold mb-3">Análisis en Tiempo Real</h3>
              <p className="text-gray-600">Observa cómo los agentes de IA colaboran en paralelo para analizar tu visión financiera completa</p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-md">
              <div className="text-accent text-2xl mb-4">🔒</div>
              <h3 className="text-xl font-semibold mb-3">Seguridad de Nivel Bancario</h3>
              <p className="text-gray-600">Tus datos están protegidos con seguridad empresarial y controles de acceso a nivel de fila</p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-md">
              <div className="text-accent text-2xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-3">Reportes Integrales</h3>
              <p className="text-gray-600">Informes detallados en markdown con gráficos interactivos y proyecciones de jubilación</p>
            </div>
          </div>
        </div>
      </section>

      {/* Sección de llamado a la acción */}
      <section className="px-8 py-20 bg-dark text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-6">
            ¿Listo para transformar tu futuro financiero?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Únete a miles de inversionistas que usan IA para optimizar sus portafolios
          </p>
          <SignUpButton mode="modal">
            <button className="px-8 py-4 bg-accent text-dark font-semibold text-lg rounded-lg hover:bg-yellow-500 transition-colors shadow-lg">
              Comienza gratis
            </button>
          </SignUpButton>
        </div>
      </section>

      {/* Pie de página */}
      <footer className="px-8 py-6 bg-gray-900 text-gray-400 text-center text-sm">
        <p>© 2025 Alex AI Financial Advisor. Todos los derechos reservados.</p>
        <p className="mt-2">
          Este consejo generado por IA no ha sido revisado por un asesor financiero calificado y no debe usarse para decisiones de inversión.
          Sólo para fines informativos.
        </p>
      </footer>
    </div>
    </>
  );
}