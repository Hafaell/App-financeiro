import { useEffect, useState } from 'react'
import { Carregando } from '../componentes/ui'
import { supabase } from '../lib/supabase'

type Detalhes = { cliente: string; email: string; escopos: string[] }

/** Tela "Permitir acesso?" do login do Claude (OAuth do Supabase). O Supabase manda para cá com ?authorization_id=. */
export function Consentimento() {
  const id = new URLSearchParams(window.location.search).get('authorization_id')
  const [detalhes, setDetalhes] = useState<Detalhes | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    if (!supabase || !id) {
      setErro('Pedido de acesso inválido. Volte ao Claude e tente conectar de novo.')
      return
    }
    supabase.auth.oauth.getAuthorizationDetails(id).then(({ data, error }) => {
      if (error || !data) return setErro(error?.message || 'Não consegui abrir o pedido de acesso.')
      if (data.redirect_url) { window.location.href = data.redirect_url; return }  // já autorizado antes
      setDetalhes({ cliente: data.client.name, email: data.user.email, escopos: data.scope.split(' ').filter(Boolean) })
    })
  }, [id])

  const responder = async (aprovar: boolean) => {
    if (!supabase || !id) return
    setOcupado(true)
    const { data, error } = aprovar
      ? await supabase.auth.oauth.approveAuthorization(id)
      : await supabase.auth.oauth.denyAuthorization(id)
    if (error || !data) {
      setErro(error?.message || 'Não consegui concluir. Tente de novo.')
      setOcupado(false)
      return
    }
    window.location.href = data.redirect_url
  }

  return (
    <div className="tela-cheia tela-login">
      <div className="cartao-login">
        <div className="marca marca-login">
          <span className="marca-selo" aria-hidden="true">CF</span>
          <strong>Controle Financeiro</strong>
        </div>
        <h1>Permitir acesso?</h1>
        {erro && <p className="erro-form" role="alert">{erro}</p>}
        {!erro && !detalhes && <Carregando />}
        {detalhes && (
          <>
            <p><strong>{detalhes.cliente}</strong> quer ver e alterar os seus dados financeiros (compras, empréstimos,
              caixinhas) como a conta <strong>{detalhes.email}</strong>.</p>
            <p className="suave">Só autorize se foi você que pediu essa conexão no Claude.</p>
            <button className="botao primario largo" disabled={ocupado} onClick={() => responder(true)}>
              {ocupado ? 'Aguarde…' : 'Permitir'}
            </button>
            <button className="botao-link" disabled={ocupado} onClick={() => responder(false)}>Negar</button>
          </>
        )}
      </div>
    </div>
  )
}
