import { FormEvent, useState } from 'react'
import { supabase } from '../lib/supabase'

/** Entrar ou criar conta, com as mesmas contas do app desktop (Supabase Auth). */
export function Login() {
  const [modo, setModo] = useState<'entrar' | 'criar'>('entrar')
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [mensagem, setMensagem] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  const enviar = async (e: FormEvent) => {
    e.preventDefault()
    if (!supabase) return
    setOcupado(true)
    setErro(null)
    setMensagem(null)
    try {
      if (modo === 'entrar') {
        const { error } = await supabase.auth.signInWithPassword({ email, password: senha })
        if (error) throw new Error(traduzir(error.message))
      } else {
        if (senha.length < 6) throw new Error('Use uma senha de pelo menos 6 caracteres.')
        const { data, error } = await supabase.auth.signUp({
          email, password: senha,
          options: { data: { nome: nome.trim() || undefined }, emailRedirectTo: window.location.origin },
        })
        if (error) throw new Error(traduzir(error.message))
        if (!data.session) {
          setMensagem('Conta criada. Abra o e-mail de confirmação que enviamos e depois entre aqui.')
          setModo('entrar')
        }
      }
    } catch (err) {
      setErro(err instanceof Error ? err.message : String(err))
    } finally {
      setOcupado(false)
    }
  }

  const criar = modo === 'criar'
  return (
    <div className="tela-cheia tela-login">
      <form className="cartao-login" onSubmit={enviar}>
        <div className="marca marca-login">
          <span className="marca-selo" aria-hidden="true">CF</span>
          <strong>Controle Financeiro</strong>
        </div>
        <h1>{criar ? 'Criar conta' : 'Entrar'}</h1>
        <p className="suave">
          {criar ? 'A mesma conta serve no site e no app do computador.' : 'Use o e-mail e a senha do app do computador.'}
        </p>
        {criar && (
          <div className="campo">
            <label htmlFor="nome">Seu nome</label>
            <input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name" />
          </div>
        )}
        <div className="campo">
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
            autoComplete="email" />
        </div>
        <div className="campo">
          <label htmlFor="senha">Senha</label>
          <input id="senha" type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required
            autoComplete={criar ? 'new-password' : 'current-password'} />
        </div>
        {erro && <p className="erro-form" role="alert">{erro}</p>}
        {mensagem && <p className="ok-form" role="status">{mensagem}</p>}
        <button className="botao primario largo" disabled={ocupado}>
          {ocupado ? 'Aguarde…' : criar ? 'Criar conta' : 'Entrar'}
        </button>
        <button type="button" className="botao-link" onClick={() => {
          setModo(criar ? 'entrar' : 'criar')
          setErro(null)
        }}>
          {criar ? 'Já tenho conta' : 'Criar uma conta'}
        </button>
      </form>
    </div>
  )
}

function traduzir(m: string) {
  const t = m.toLowerCase()
  if (t.includes('invalid login')) return 'E-mail ou senha incorretos.'
  if (t.includes('email not confirmed')) return 'Confirme seu e-mail antes de entrar (veja a caixa de entrada).'
  if (t.includes('already registered')) return 'Já existe uma conta com esse e-mail. Entre com ela.'
  if (t.includes('signups not allowed')) return 'O cadastro de contas novas está desligado no Supabase.'
  if (t.includes('rate limit')) return 'Muitas tentativas seguidas. Espere um pouco e tente de novo.'
  if (t.includes('password')) return 'Senha fraca: use pelo menos 6 caracteres.'
  return m
}
