import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@clerk/nextjs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import {
  PieChart, Pie, Cell, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import Layout from '../components/Layout';
import { API_URL } from '../lib/config';
import Head from 'next/head';

interface Job {
  id: string;
  created_at: string;
  status: string;
  job_type: string;
  report_payload?: {
    agent: string;
    content: string;
    generated_at: string;
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  charts_payload?: Record<string, any> | null;  // Charter almacena los gráficos con claves dinámicas
  retirement_payload?: {
    agent: string;
    analysis: string;
    generated_at: string;
  };
  error_message?: string;
}

interface JobListItem {
  id: string;
  created_at: string;
  status: string;
  job_type: string;
}

type TabType = 'overview' | 'charts' | 'retirement';

// Paleta de colores para los gráficos
const COLORS = [
  '#209DD7', // primario
  '#753991', // acento AI
  '#FFB707', // acento
  '#062147', // oscuro
  '#60A5FA', // azul claro
  '#A78BFA', // morado claro
  '#FBBF24', // amarillo
  '#34D399', // verde
  '#F87171', // rojo
  '#94A3B8', // gris
];

export default function Analysis() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { job_id } = router.query;
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [fetchingLatest, setFetchingLatest] = useState(false);

  useEffect(() => {
    const loadJob = async (jobId: string) => {
      try {
        const token = await getToken();
        const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const jobData = await response.json();
          setJob(jobData);
        } else {
          console.error('No se pudo obtener el análisis');
        }
      } catch (error) {
        console.error('Error al obtener el análisis:', error);
      } finally {
        setLoading(false);
      }
    };

    const loadLatestJob = async () => {
      setFetchingLatest(true);
      try {
        const token = await getToken();
        // Primero, obtenemos la lista de análisis para encontrar el último completado
        const response = await fetch(`${API_URL}/api/jobs`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          const jobs: JobListItem[] = data.jobs || [];
          // Encontrar el último análisis completado
          const latestCompletedJob = jobs
            .filter(j => j.status === 'completed')
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

          if (latestCompletedJob) {
            // Cargar los detalles completos del análisis
            await loadJob(latestCompletedJob.id);
            // Actualizar la URL para incluir el job_id sin recargar la página
            router.replace(`/analysis?job_id=${latestCompletedJob.id}`, undefined, { shallow: true });
          } else {
            setLoading(false);
          }
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error('Error al obtener el último análisis:', error);
        setLoading(false);
      } finally {
        setFetchingLatest(false);
      }
    };

    if (job_id) {
      loadJob(job_id as string);
    } else if (router.isReady) {
      // El router está listo pero no se proporcionó job_id - obtener el último análisis
      loadLatestJob();
    }
  }, [job_id, router.isReady, getToken, router]);


  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-lg shadow px-8 py-12 text-center">
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-1/3 mx-auto mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-lg shadow px-8 py-12 text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {fetchingLatest ? 'Cargando el último análisis...' : 'Ningún análisis disponible'}
              </h2>
              <p className="text-gray-600 mb-6">
                {fetchingLatest
                  ? 'Por favor espera mientras cargamos tu último análisis.'
                  : 'Aún no has completado ningún análisis. Realiza un nuevo análisis para ver los resultados aquí.'}
              </p>
              {!fetchingLatest && (
                <button
                  onClick={() => router.push('/advisor-team')}
                  className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-600 font-semibold"
                >
                  Realizar nuevo análisis
                </button>
              )}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (job.status === 'running' || job.status === 'pending') {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-lg shadow px-8 py-12 text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Análisis en progreso</h2>
              <p className="text-gray-600 mb-6">Tu análisis aún se está procesando. Por favor revisa de nuevo en unos minutos.</p>
              <div className="flex justify-center space-x-2 mb-6">
                <div className="w-3 h-3 bg-ai-accent rounded-full animate-pulse"></div>
                <div className="w-3 h-3 bg-ai-accent rounded-full animate-pulse delay-75"></div>
                <div className="w-3 h-3 bg-ai-accent rounded-full animate-pulse delay-150"></div>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-600 font-semibold"
              >
                Refrescar
              </button>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (job.status === 'failed') {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-lg shadow px-8 py-12">
              <h2 className="text-2xl font-bold text-red-600 mb-4">El análisis ha fallado</h2>
              <p className="text-gray-600 mb-4">El análisis encontró un error y no pudo completarse.</p>
              {job.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-red-800">{job.error_message}</p>
                </div>
              )}
              <button
                onClick={() => router.push('/advisor-team')}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-600 font-semibold"
              >
                Probar otro análisis
              </button>
            </div>
          </div>
        </div>
      </Layout>
    );
  }


  // Renderizadores de contenido de pestañas
  const renderOverview = () => {
    const report = job?.report_payload?.content;
    if (!report) {
      return (
        <div className="text-center py-12 text-gray-500">
          No hay informe de portafolio disponible.
        </div>
      );
    }

    return (
      <div className="prose prose-lg max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkBreaks]}
          components={{
            h1: ({children}) => <h1 className="text-3xl font-bold mb-4 text-gray-900">{children}</h1>,
            h2: ({children}) => <h2 className="text-2xl font-semibold mb-3 text-gray-800 mt-6">{children}</h2>,
            h3: ({children}) => <h3 className="text-xl font-medium mb-2 text-gray-700 mt-4">{children}</h3>,
            ul: ({children}) => <ul className="list-disc ml-6 mb-4 space-y-1">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal ml-6 mb-4 space-y-1">{children}</ol>,
            li: ({children}) => <li className="text-gray-700">{children}</li>,
            p: ({children}) => <p className="mb-4 text-gray-700 leading-relaxed">{children}</p>,
            table: ({children}) => (
              <div className="overflow-x-auto mb-6">
                <table className="w-full border-collapse">{children}</table>
              </div>
            ),
            thead: ({children}) => <thead className="bg-gray-100">{children}</thead>,
            th: ({children}) => <th className="p-3 text-left font-semibold border border-gray-300">{children}</th>,
            td: ({children}) => <td className="p-3 border border-gray-300">{children}</td>,
            strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
            blockquote: ({children}) => (
              <blockquote className="border-l-4 border-primary pl-4 my-4 italic text-gray-600">
                {children}
              </blockquote>
            ),
          }}
        >
          {report}
        </ReactMarkdown>
      </div>
    );
  };

  const renderCharts = () => {
    const chartsPayload = job?.charts_payload;
    if (!chartsPayload || Object.keys(chartsPayload).length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          No hay datos de gráficos disponibles.
        </div>
      );
    }

    // Función auxiliar para formatear títulos de los gráficos desde la clave
    const formatTitle = (key: string): string => {
      return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };

    // Función auxiliar para determinar el tipo de gráfico basándose en la estructura de datos o metadatos
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const getChartType = (chartData: any): 'pie' | 'donut' | 'bar' | 'horizontalBar' | 'line' => {
      // Si el agente charter especifica un tipo, usarlo directamente si se soporta
      if (chartData.type) {
        const supportedTypes = ['pie', 'donut', 'bar', 'horizontalBar', 'line'];
        if (supportedTypes.includes(chartData.type)) {
          return chartData.type;
        }
        // Mapear variaciones a tipos soportados
        const typeMap: Record<string, 'pie' | 'donut' | 'bar' | 'horizontalBar' | 'line'> = {
          'column': 'bar',
          'area': 'line'
        };
        if (typeMap[chartData.type]) {
          return typeMap[chartData.type];
        }
      }

      // Si los datos tienen fechas/series temporales, usar gráfico de líneas
      if (chartData.data?.[0]?.date || chartData.data?.[0]?.year) return 'line';

      // Si los datos representan partes de un todo (tienen porcentajes o conjunto pequeño), usar pie
      if (chartData.data?.length <= 10 && chartData.data?.[0]?.value) return 'pie';

      // Por defecto, usar gráfico de barras para otros casos
      return 'bar';
    };

    // Generar dinámicamente todos los gráficos proporcionados por el agente charter
    const chartEntries = Object.entries(chartsPayload);

    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {chartEntries.map(([key, chartData]: [string, any]) => {
          // Omitir si no hay datos
          if (!chartData?.data || chartData.data.length === 0) return null;

          const chartType = getChartType(chartData);
          const title = chartData.title || formatTitle(key);

          return (
            <div key={key} className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="text-xl font-semibold mb-4 text-gray-800">{title}</h3>
              <ResponsiveContainer width="100%" height={300}>
                {chartType === 'pie' || chartType === 'donut' ? (
                  <PieChart>
                    <Pie
                      data={chartData.data}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label
                      outerRadius={100}
                      innerRadius={chartType === 'donut' ? 60 : 0}  // El donut tiene inner radius
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                      {chartData.data.map((entry: any, idx: number) => (
                        <Cell key={`cell-${idx}`} fill={entry.color || COLORS[idx % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString('es-ES')}`} />
                  </PieChart>
                ) : chartType === 'horizontalBar' ? (
                  // Para las barras horizontales, utilizamos barras verticales normales con etiquetas rotadas
                  // El layout horizontal de recharts puede ser problemático
                  <BarChart
                    data={chartData.data}
                    margin={{ left: 10, right: 30, top: 5, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      angle={-45}
                      textAnchor="end"
                      interval={0}
                      height={60}
                    />
                    <YAxis
                      tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                    />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString('es-ES')}`} />
                    <Bar dataKey="value">
                      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                      {chartData.data?.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                ) : chartType === 'bar' ? (
                  <BarChart data={chartData.data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString('es-ES')}`} />
                    <Bar dataKey="value" fill={chartData.color || COLORS[0]} />
                  </BarChart>
                ) : (
                  // Gráfico de líneas para datos temporales
                  <LineChart data={chartData.data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={chartData.xKey || "year"} />
                    <YAxis tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString('es-ES')}`} />
                    <Line type="monotone" dataKey="value" stroke={COLORS[0]} strokeWidth={2} />
                  </LineChart>
                )}
              </ResponsiveContainer>

              {/* Agregar leyenda para gráficos pie/donut con muchos elementos */}
              {(chartType === 'pie' || chartType === 'donut') && chartData.data.length > 6 && (
                <div className="mt-4 grid grid-cols-2 gap-2">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {chartData.data.map((entry: any, idx: number) => (
                    <div key={entry.name} className="flex items-center text-sm">
                      <div
                        className="w-3 h-3 rounded-full mr-2"
                        style={{ backgroundColor: entry.color || COLORS[idx % COLORS.length] }}
                      />
                      <span className="text-gray-600">{entry.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderRetirement = () => {
    const retirement = job?.retirement_payload;
    if (!retirement) {
      return (
        <div className="text-center py-12 text-gray-500">
          No hay proyección de jubilación disponible.
        </div>
      );
    }

    // El backend proporciona 'analysis' como texto markdown
    const retirementAnalysis = retirement.analysis;

    return (
      <div className="space-y-8">
        {/* Sección de análisis */}
        {retirementAnalysis && (
          <div className="bg-ai-accent/10 border border-ai-accent/20 rounded-lg p-6">
            <div className="prose prose-lg max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkBreaks]}
                components={{
                  h2: ({children}) => <h2 className="text-2xl font-semibold mb-3 text-gray-800">{children}</h2>,
                  h3: ({children}) => <h3 className="text-xl font-medium mb-2 text-gray-700">{children}</h3>,
                  p: ({children}) => <p className="text-gray-700 leading-relaxed mb-4">{children}</p>,
                  strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                  ul: ({children}) => <ul className="list-disc ml-6 mt-2 space-y-1">{children}</ul>,
                  li: ({children}) => <li className="text-gray-700">{children}</li>,
                }}
              >
                {retirementAnalysis}
              </ReactMarkdown>
            </div>
          </div>
        )}

      </div>
    );
  };

  return (
    <>
      <Head>
        <title>Análisis - Alex AI Asesor Financiero</title>
      </Head>
      <Layout>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Encabezado */}
          <div className="bg-white rounded-lg shadow px-8 py-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-dark mb-2">Resultados del análisis de portafolio</h1>
                <p className="text-gray-600">
                  Completado el {formatDate(job.created_at)}
                </p>
              </div>
              <button
                onClick={() => router.push('/advisor-team')}
                className="px-6 py-3 bg-ai-accent text-white rounded-lg hover:bg-purple-700 font-semibold"
              >
                Nuevo análisis
              </button>
            </div>
          </div>

          {/* Pestañas */}
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-3 px-8 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'overview'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  📊 Resumen
                </button>
                <button
                  onClick={() => setActiveTab('charts')}
                  className={`py-3 px-8 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'charts'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  📈 Gráficos
                </button>
                <button
                  onClick={() => setActiveTab('retirement')}
                  className={`py-3 px-8 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'retirement'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  🎯 Proyección de Jubilación
                </button>
              </nav>
            </div>
          </div>

          {/* Contenido de pestañas */}
          <div className="bg-white rounded-lg shadow px-8 py-6">
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'charts' && renderCharts()}
            {activeTab === 'retirement' && renderRetirement()}
          </div>
        </div>
      </div>
      </Layout>
    </>
  );
}