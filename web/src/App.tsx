import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { Carregando, ErroCarga } from './componentes/ui'
import { Estrutura, useRota } from './componentes/estrutura'
import { get } from './lib/api'
import { ProvedorEstado } from './lib/estado'
import { configurado, MODO_LOCAL, supabase } from './lib/supabase'
import type { Inicio } from './lib/tipos'
import { Consentimento } from './paginas/Consentimento'
import { Login } from './paginas/Login'
import { VisaoGeral } from './paginas/VisaoGeral'
import { Transacoes } from './paginas/Transacoes'
import { ReceitasDespesas } from './paginas/ReceitasDespesas'
import { Planejamento } from './paginas/Planejamento'
import { Comparativo } from './paginas/Comparativo'
import { Emprestimos } from './paginas/Emprestimos'
import { Caixinhas } from './paginas/Caixinhas'
import { Importar } from './paginas/Importar'
import { Ferramentas } from './paginas/Ferramentas'

const PAGINAS: Record<string, () => JSX.Element> = {
  '/': VisaoGeral,
  '/transacoes': Transacoes,
  '/receitas-e-despesas': ReceitasDespesas,
  '/planejamento': Planejamento,
  '/comparativo': Comparativo,
  '/emprestimos': Emprestimos,
  '/caixinhas': Caixinhas,
  '/importar': Importar,
  '/ferramentas': Ferramentas,
}

export function App() {
  const [sessao, setSessao] = useState<Session | null | undefined>(MODO_LOCAL ? null : undefined)

  useEffect(() => {
    if (!supabase) return
    supabase.auth.getSession().then(({ data }) => setSessao(data.session))
    const { data } = supabase.auth.onAuthStateChange((_evento, s) => setSessao(s))
    return () => data.subscription.unsubscribe()
  }, [])

  if (!configurado) {
    return (
      <div className="tela-cheia">
        <div className="cartao-login">
          <h1>Falta configurar o site</h1>
          <p className="suave">
            Defina as variáveis VITE_SUPABASE_URL e VITE_SUPABASE_CHAVE no Vercel (Settings &gt; Environment
            Variables) e publique de novo.
          </p>
        </div>
      </div>
    )
  }
  if (sessao === undefined) return <div className="tela-cheia"><Carregando /></div>
  if (!MODO_LOCAL && !sessao) return <Login />
  if (window.location.pathname === '/oauth/consent') return <Consentimento />

  const meta = sessao?.user.user_metadata as { nome?: string } | undefined
  const nome = MODO_LOCAL ? 'Modo local' : meta?.nome || sessao?.user.email || ''
  return <Conectado key={sessao?.user.id ?? 'local'} nome={nome} />
}

function Conectado({ nome }: { nome: string }) {
  const [inicio, setInicio] = useState<Inicio | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [tentativa, setTentativa] = useState(0)
  const [rota, ir] = useRota()

  useEffect(() => {
    setErro(null)
    get<Inicio>('/api/inicio').then(setInicio).catch((e) => setErro(e.message))
  }, [tentativa])

  if (erro) {
    return (
      <div className="tela-cheia">
        <ErroCarga mensagem={`Não consegui abrir seus dados. ${erro}`} tentarDeNovo={() => setTentativa((t) => t + 1)} />
      </div>
    )
  }
  if (!inicio) return <div className="tela-cheia"><Carregando /></div>

  const Pagina = PAGINAS[rota]
  const sair = supabase ? () => void supabase!.auth.signOut() : undefined
  return (
    <ProvedorEstado inicio={inicio}>
      <Estrutura atual={rota} ir={ir} nome={nome} sair={sair}>
        <Pagina key={rota} />
      </Estrutura>
    </ProvedorEstado>
  )
}
