import { useAuth } from "@clerk/nextjs";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";
import ConfirmModal from "../components/ConfirmModal";
import { API_URL } from "../lib/config";
import { SkeletonTable } from "../components/Skeleton";
import Head from "next/head";

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  current_price?: number;
}

interface Account {
  id: string;
  account_name: string;
  account_purpose: string;
  cash_balance: number;
  positions?: Position[];
}

export default function Accounts() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [populatingData, setPopulatingData] = useState(false);
  const [resettingAccounts, setResettingAccounts] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAccount, setNewAccount] = useState({ name: '', purpose: '', cash_balance: '' });
  const [savingAccount, setSavingAccount] = useState(false);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    type: 'reset' | 'delete';
    accountId?: string;
    accountName?: string;
  }>({ isOpen: false, type: 'reset' });

  const loadAccounts = useCallback(async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Cuentas recibidas desde la API:', data);
        // Para cada cuenta, cargar posiciones
        const accountsWithPositions = await Promise.all(
          data.map(async (account: Account) => {
            console.log('Procesando cuenta:', account.id, account.account_name);
            // Saltar si la cuenta no tiene ID
            if (!account.id) {
              console.warn('Cuenta sin ID:', account);
              return { ...account, positions: [] };
            }

            try {
              const positionsResponse = await fetch(
                `${API_URL}/api/accounts/${account.id}/positions`,
                {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                  },
                }
              );
              if (positionsResponse.ok) {
                const data = await positionsResponse.json();
                const positions = data.positions || [];
                console.log(`Cargadas ${positions.length} posiciones para la cuenta ${account.id}`);
                return { ...account, positions };
              }
            } catch (err) {
              console.error(`Error al cargar posiciones para la cuenta ${account.id}:`, err);
            }
            return { ...account, positions: [] };
          })
        );
        console.log('Cuentas finales con posiciones:', accountsWithPositions);
        setAccounts(accountsWithPositions);
      }
    } catch (error) {
      console.error('Error cargando cuentas:', error);
      setMessage({ type: 'error', text: 'No se pudieron cargar las cuentas' });
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  // Escuchar eventos de finalización de análisis para refrescar datos
  useEffect(() => {
    const handleAnalysisCompleted = () => {
      // Refrescar cuentas para obtener precios actualizados tras el análisis
      console.log('Análisis completado - refrescando cuentas...');
      loadAccounts();
    };

    // Escuchar el evento de finalización
    window.addEventListener('analysis:completed', handleAnalysisCompleted);

    return () => {
      window.removeEventListener('analysis:completed', handleAnalysisCompleted);
    };
  }, [loadAccounts]);

  const populateTestData = async () => {
    setPopulatingData(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/populate-test-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        await loadAccounts(); // Recargar cuentas después de poblar datos
      } else {
        setMessage({ type: 'error', text: 'No se pudieron poblar los datos de prueba' });
      }
    } catch (error) {
      console.error('Error al poblar datos de prueba:', error);
      setMessage({ type: 'error', text: 'Error al poblar datos de prueba' });
    } finally {
      setPopulatingData(false);
    }
  };

  const resetAccounts = async () => {
    setResettingAccounts(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/reset-accounts`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        // Limpiar cuentas inmediatamente después de un reseteo exitoso
        setAccounts([]);
        // Luego recargar para confirmar estado vacío
        await loadAccounts();
      } else {
        setMessage({ type: 'error', text: 'No se pudieron reiniciar las cuentas' });
      }
    } catch (error) {
      console.error('Error al reiniciar cuentas:', error);
      setMessage({ type: 'error', text: 'Error al reiniciar cuentas' });
    } finally {
      setResettingAccounts(false);
    }
  };

  const calculateAccountTotal = (account: Account) => {
    const positionsValue = account.positions?.reduce((sum, position) => {
      const value = Number(position.quantity) * (Number(position.current_price) || 0);
      return sum + value;
    }, 0) || 0;
    return Number(account.cash_balance) + positionsValue;
  };

  const calculatePortfolioTotal = () => {
    return accounts.reduce((sum, account) => sum + calculateAccountTotal(account), 0);
  };

  const handleAddAccount = async () => {
    if (!newAccount.name.trim()) {
      setMessage({ type: 'error', text: 'Por favor ingresa un nombre de cuenta' });
      return;
    }

    setSavingAccount(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_name: newAccount.name,
          account_purpose: newAccount.purpose || 'Cuenta de inversión',
          cash_balance: parseFloat(newAccount.cash_balance.replace(/,/g, '')) || 0,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Cuenta creada exitosamente' });
        setShowAddModal(false);
        setNewAccount({ name: '', purpose: '', cash_balance: '' });
        await loadAccounts();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'No se pudo crear la cuenta' });
      }
    } catch (error) {
      console.error('Error al crear cuenta:', error);
      setMessage({ type: 'error', text: 'Error al crear cuenta' });
    } finally {
      setSavingAccount(false);
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    setDeletingAccountId(accountId);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts/${accountId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Cuenta eliminada exitosamente' });
        await loadAccounts();
      } else {
        setMessage({ type: 'error', text: 'No se pudo eliminar la cuenta' });
      }
    } catch (error) {
      console.error('Error eliminando la cuenta:', error);
      setMessage({ type: 'error', text: 'Error eliminando la cuenta' });
    } finally {
      setDeletingAccountId(null);
    }
  };

  const formatCurrencyInput = (value: string) => {
    // Eliminar caracteres no numéricos excepto decimal
    const cleaned = value.replace(/[^0-9.]/g, '');
    // Formatear con comas
    const parts = cleaned.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  };

  return (
    <>
      <Head>
        <title>Cuentas - Alex AI Financial Advisor</title>
      </Head>
      <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-dark">Cuentas de Inversión</h2>
              <p className="text-sm text-gray-600 mt-1">Administra tus cuentas y portafolios de inversión</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Añadir Cuenta
              </button>
              {accounts.length === 0 && !loading && (
                <button
                  onClick={populateTestData}
                  disabled={populatingData}
                  className="bg-accent hover:bg-yellow-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {populatingData ? 'Poblando...' : 'Poblar Datos de Prueba'}
                </button>
              )}
              {accounts.length > 0 && (
                <button
                  onClick={() => setConfirmModal({ isOpen: true, type: 'reset' })}
                  disabled={resettingAccounts}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {resettingAccounts ? 'Reiniciando...' : 'Reiniciar Todas'}
                </button>
              )}
            </div>
          </div>

          {message && (
            <div className={`mb-4 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200 text-green-700'
                : 'bg-red-50 border border-red-200 text-red-700'
            }`}>
              {message.text}
            </div>
          )}

          {loading ? (
            <SkeletonTable rows={3} />
          ) : accounts.length === 0 ? (
            <div className="bg-primary/10 border border-primary/20 rounded-lg p-6 text-center">
              <p className="text-primary font-semibold mb-2">
                No se encontraron cuentas
              </p>
              <p className="text-sm text-gray-600">
                Haz clic en el botón &quot;Poblar Datos de Prueba&quot; de arriba para crear cuentas de muestra con posiciones
              </p>
            </div>
          ) : (
            <>
              {/* Resumen del Portafolio */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Valor Total del Portafolio</p>
                    <p className="text-2xl font-bold text-primary">
                      ${calculatePortfolioTotal().toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Cantidad de Cuentas</p>
                    <p className="text-2xl font-bold text-dark">{accounts.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Total de Posiciones</p>
                    <p className="text-2xl font-bold text-dark">
                      {accounts.reduce((sum, acc) => sum + (acc.positions?.length || 0), 0)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Tabla de cuentas */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700">Nombre de Cuenta</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 hidden md:table-cell">Tipo</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">Posiciones</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">Efectivo</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700">Valor Total</th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-700">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((account) => {
                      const positionsValue = calculateAccountTotal(account) - Number(account.cash_balance);
                      return (
                        <tr key={account.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                          <td className="py-4 px-4">
                            <div>
                              <p className="font-semibold text-dark">{account.account_name}</p>
                              <p className="text-xs text-gray-500 md:hidden">{account.account_purpose}</p>
                            </div>
                          </td>
                          <td className="py-4 px-4 hidden md:table-cell">
                            <span className="text-sm text-gray-600">{account.account_purpose}</span>
                          </td>
                          <td className="py-4 px-4 text-right">
                            <div>
                              <p className="font-medium">{account.positions?.length || 0}</p>
                              {positionsValue > 0 && (
                                <p className="text-xs text-gray-500">
                                  ${positionsValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                </p>
                              )}
                            </div>
                          </td>
                          <td className="py-4 px-4 text-right">
                            ${Number(account.cash_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-4 px-4 text-right">
                            <p className="font-semibold text-primary">
                              ${calculateAccountTotal(account).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex justify-center gap-2">
                              <button
                                onClick={() => router.push(`/accounts/${account.id}`)}
                                className="text-primary hover:bg-primary/10 p-2 rounded transition-colors"
                                title="Ver/Editar"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => setConfirmModal({
                                  isOpen: true,
                                  type: 'delete',
                                  accountId: account.id,
                                  accountName: account.account_name
                                })}
                                disabled={deletingAccountId === account.id}
                                className="text-red-600 hover:bg-red-50 p-2 rounded transition-colors disabled:opacity-50"
                                title="Eliminar"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Modal para Añadir Cuenta */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-dark mb-4">Añadir Nueva Cuenta</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre de Cuenta *
                  </label>
                  <input
                    type="text"
                    value={newAccount.name}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="ej: 401k, Roth IRA, Corretaje"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Propósito de la Cuenta
                  </label>
                  <input
                    type="text"
                    value={newAccount.purpose}
                    onChange={(e) => setNewAccount({ ...newAccount, purpose: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="ej: Crecimiento a largo plazo, Retiro"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Saldo Inicial en Efectivo
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="text"
                      value={newAccount.cash_balance}
                      onChange={(e) => setNewAccount({ ...newAccount, cash_balance: formatCurrencyInput(e.target.value) })}
                      className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              {message && message.type === 'error' && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {message.text}
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleAddAccount}
                  disabled={savingAccount}
                  className="flex-1 bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {savingAccount ? 'Creando...' : 'Crear Cuenta'}
                </button>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setNewAccount({ name: '', purpose: '', cash_balance: '' });
                    setMessage(null);
                  }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Confirmación */}
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          title={confirmModal.type === 'reset' ? 'Reiniciar Todas las Cuentas' : 'Eliminar Cuenta'}
          message={
            confirmModal.type === 'reset' ? (
              <div>
                <p className="font-semibold mb-2">¿Estás seguro de que deseas eliminar todas tus cuentas?</p>
                <p className="text-sm">Esto eliminará permanentemente:</p>
                <ul className="list-disc list-inside text-sm mt-1 ml-2">
                  <li>Todas las {accounts.length} cuenta{accounts.length !== 1 ? 's' : ''}</li>
                  <li>Todas las posiciones en esas cuentas</li>
                  <li>Todo el historial de transacciones</li>
                </ul>
                <p className="text-sm mt-3 text-red-600 font-semibold">Esta acción no se puede deshacer.</p>
              </div>
            ) : (
              <div>
                <p>¿Estás seguro de que deseas eliminar <span className="font-semibold">&ldquo;{confirmModal.accountName}&rdquo;</span>?</p>
                <p className="text-sm mt-2">Esto también eliminará todas las posiciones en esta cuenta.</p>
                <p className="text-sm mt-2 text-red-600 font-semibold">Esta acción no se puede deshacer.</p>
              </div>
            )
          }
          confirmText={confirmModal.type === 'reset' ? 'Eliminar Todas las Cuentas' : 'Eliminar Cuenta'}
          cancelText="Cancelar"
          confirmButtonClass="bg-red-600 hover:bg-red-700"
          onConfirm={() => {
            if (confirmModal.type === 'reset') {
              resetAccounts();
            } else if (confirmModal.accountId) {
              handleDeleteAccount(confirmModal.accountId);
            }
            setConfirmModal({ isOpen: false, type: 'reset' });
          }}
          onCancel={() => setConfirmModal({ isOpen: false, type: 'reset' })}
          isProcessing={resettingAccounts || deletingAccountId !== null}
        />
      </div>
      </Layout>
    </>
  );
}