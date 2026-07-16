from fpdf import FPDF
import os

class PDFFluxosAtendimento(FPDF):
    def __init__(self):
        super().__init__('L', 'mm', 'A4')  # Mudado para Landscape (paisagem)
        self.set_auto_page_break(True, 12)
        # Cores institucionais
        self.cor_primaria = (0, 51, 102)
        self.cor_secundaria = (0, 102, 102)
        self.cor_destaque = (204, 0, 0)
        self.cor_fundo_tabela = (230, 240, 250)
        self.cor_fundo_tabela2 = (240, 245, 255)
        self.cor_borda = (100, 100, 100)
        
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 7)
            self.set_text_color(128, 128, 128)
            self.cell(0, 4, 'Sistema Maria Gercina - Fluxos de Atendimento - Hospital Municipal de Tracunhaém/PE', align='C')
            self.ln(5)
    
    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')
    
    def titulo_principal(self):
        self.set_fill_color(*self.cor_primaria)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 20)
        self.cell(0, 14, 'FLUXOS DE ATENDIMENTO', align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Sistema Maria Gercina', align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self.cor_primaria)
        self.cell(0, 7, 'Hospital Municipal - Secretaria de Saúde de Tracunhaém/PE', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.set_text_color(0, 0, 0)
    
    def secao_titulo(self, titulo, cor=None):
        if cor is None:
            cor = self.cor_primaria
        self.set_fill_color(*cor)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 7, f'  {titulo}', fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)
    
    def subtitulo(self, texto):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self.cor_secundaria)
        self.cell(0, 5, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_text_color(0, 0, 0)
    
    def texto_normal(self, texto, bold=False, size=8):
        if bold:
            self.set_font('Helvetica', 'B', size)
        else:
            self.set_font('Helvetica', '', size)
        self.multi_cell(0, 4.5, texto, align='L')
        self.ln(1)
    
    def tabela_cabecalho(self, colunas, larguras):
        self.set_fill_color(*self.cor_primaria)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 7)
        self.set_draw_color(*self.cor_borda)
        self.set_line_width(0.2)
        
        for col, larg in zip(colunas, larguras):
            self.cell(larg, 6, col, border=1, fill=True, align='C')
        self.ln()
        self.set_text_color(0, 0, 0)
    
    def tabela_linha(self, dados, larguras, fill=False, bold_first=False):
        if fill:
            self.set_fill_color(*self.cor_fundo_tabela)
        else:
            self.set_fill_color(*self.cor_fundo_tabela2)
        
        self.set_font('Helvetica', '', 7)
        self.set_draw_color(*self.cor_borda)
        self.set_line_width(0.2)
        
        # Calcular altura necessária para cada célula
        alturas_celulas = []
        for dado, larg in zip(dados, larguras):
            # Calcular quantas linhas o texto vai ocupar
            texto = str(dado)
            largura_util = larg - 2  # Margem interna de 1mm de cada lado
            
            # Usar multi_cell para calcular altura
            # Estimativa: cada caractere ~1.8mm de largura na fonte 7
            caracteres_por_linha = max(1, int(largura_util / 1.8))
            num_linhas = max(1, -(-len(texto) // caracteres_por_linha))  # Ceiling division
            altura = num_linhas * 4 + 2  # 4mm por linha + margem
            alturas_celulas.append(altura)
        
        altura_linha = max(alturas_celulas)
        
        # Desenhar cada célula com altura calculada
        x_inicial = self.get_x()
        y_inicial = self.get_y()
        
        for i, (dado, larg) in enumerate(zip(dados, larguras)):
            x = x_inicial + sum(larguras[:i])
            
            # Desenhar retângulo da célula
            self.rect(x, y_inicial, larg, altura_linha, 'DF')
            
            # Escrever texto dentro da célula
            self.set_xy(x + 1, y_inicial + 1)
            if bold_first and i == 0:
                self.set_font('Helvetica', 'B', 7)
            else:
                self.set_font('Helvetica', '', 7)
            
            # Multi_cell dentro dos limites da célula
            self.multi_cell(larg - 2, 4, str(dado), align='C' if i == 0 else 'L')
        
        # Voltar para o início da próxima linha
        self.set_xy(x_inicial, y_inicial + altura_linha)
        self.set_line_width(0.2)
    
    def desenhar_fluxograma(self, titulo, etapas, labels, setas_duplas=None):
        if setas_duplas is None:
            setas_duplas = []
        
        self.subtitulo(titulo)
        
        # Largura total disponível (A4 paisagem = 297mm, margens 15mm cada lado)
        largura_total = 267
        x_inicial = 15
        n_etapas = len(etapas)
        
        # Ajustar tamanhos baseado no número de etapas
        if n_etapas <= 4:
            largura_caixa = 50
            largura_seta = 15
        elif n_etapas <= 5:
            largura_caixa = 42
            largura_seta = 12
        elif n_etapas <= 7:
            largura_caixa = 31
            largura_seta = 8
        else:
            largura_caixa = 28
            largura_seta = 6
        
        altura_caixa = 12
        altura_label = 4
        
        y_inicial = self.get_y()
        
        self.set_draw_color(*self.cor_borda)
        self.set_line_width(0.3)
        
        for i, (etapa, label) in enumerate(zip(etapas, labels)):
            # Calcular posição X
            x = x_inicial + i * (largura_caixa + largura_seta)
            
            # Verificar se não ultrapassa a margem direita (285mm)
            if x + largura_caixa > 285:
                break
            
            # Cor da caixa baseada no tipo
            if '✅' in etapa or etapa == 'Alta':
                self.set_fill_color(46, 125, 50)
                self.set_text_color(255, 255, 255)
            elif 'Medicação' in etapa or 'Observação' in etapa or 'Observacao' in etapa or 'Medic.' in etapa or 'Sala' in etapa:
                self.set_fill_color(255, 152, 0)
                self.set_text_color(255, 255, 255)
            elif 'Médico' in etapa or 'Medico' in etapa:
                self.set_fill_color(25, 118, 210)
                self.set_text_color(255, 255, 255)
            elif 'Triagem' in etapa:
                self.set_fill_color(123, 31, 162)
                self.set_text_color(255, 255, 255)
            elif 'Recepção' in etapa or 'Recepcao' in etapa:
                self.set_fill_color(0, 150, 136)
                self.set_text_color(255, 255, 255)
            elif 'Transfer' in etapa:
                self.set_fill_color(211, 47, 47)
                self.set_text_color(255, 255, 255)
            elif 'Internação' in etapa or 'Internacao' in etapa:
                self.set_fill_color(255, 87, 34)
                self.set_text_color(255, 255, 255)
            elif 'Óbito' in etapa or 'Obito' in etapa:
                self.set_fill_color(0, 0, 0)
                self.set_text_color(255, 255, 255)
            else:
                self.set_fill_color(*self.cor_primaria)
                self.set_text_color(255, 255, 255)
            
            # Desenhar retângulo
            self.rect(x, y_inicial, largura_caixa, altura_caixa, 'DF')
            
            # Texto na caixa
            self.set_font('Helvetica', 'B', 6)
            texto_etapa = etapa[:20]
            largura_texto = self.get_string_width(texto_etapa)
            
            if largura_texto > largura_caixa - 2:
                # Se o texto é muito largo, usar multi_cell
                self.set_xy(x + 1, y_inicial + 1)
                self.multi_cell(largura_caixa - 2, 3.5, texto_etapa, align='C')
            else:
                self.set_xy(x + (largura_caixa - largura_texto) / 2, y_inicial + 3)
                self.cell(largura_texto, 4, texto_etapa)
            
            # Label abaixo da caixa
            self.set_text_color(*self.cor_secundaria)
            self.set_font('Helvetica', '', 5.5)
            texto_label = label[:22]
            largura_label_texto = self.get_string_width(texto_label)
            
            if largura_label_texto > largura_caixa - 2:
                self.set_xy(x + 1, y_inicial + altura_caixa + 1)
                self.multi_cell(largura_caixa - 2, 3, texto_label, align='C')
            else:
                self.set_xy(x + (largura_caixa - largura_label_texto) / 2, y_inicial + altura_caixa + 1)
                self.cell(largura_label_texto, 3, texto_label)
            
            # Desenhar seta
            if i < n_etapas - 1:
                x_seta = x + largura_caixa
                y_centro = y_inicial + altura_caixa / 2
                
                self.set_draw_color(*self.cor_borda)
                self.set_line_width(0.5)
                
                if i in setas_duplas:
                    # Seta dupla
                    self.line(x_seta + 1, y_centro - 2, x_seta + largura_seta - 1, y_centro - 2)
                    self.line(x_seta + largura_seta - 1, y_centro - 2, x_seta + largura_seta - 3, y_centro - 4)
                    self.line(x_seta + largura_seta - 1, y_centro - 2, x_seta + largura_seta - 3, y_centro)
                    
                    self.line(x_seta + largura_seta - 1, y_centro + 2, x_seta + 1, y_centro + 2)
                    self.line(x_seta + 1, y_centro + 2, x_seta + 3, y_centro)
                    self.line(x_seta + 1, y_centro + 2, x_seta + 3, y_centro + 4)
                else:
                    # Seta simples
                    self.line(x_seta + 1, y_centro, x_seta + largura_seta - 1, y_centro)
                    self.line(x_seta + largura_seta - 1, y_centro, x_seta + largura_seta - 3, y_centro - 3)
                    self.line(x_seta + largura_seta - 1, y_centro, x_seta + largura_seta - 3, y_centro + 3)
        
        self.set_text_color(0, 0, 0)
        self.set_y(y_inicial + altura_caixa + altura_label + 10)
        
        # Linha separadora
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(15, self.get_y(), 282, self.get_y())
        self.ln(4)

# Criar PDF
pdf = PDFFluxosAtendimento()
pdf.alias_nb_pages()
pdf.add_page()

# Título principal
pdf.titulo_principal()

# ============ SEÇÃO: ATORES DO SISTEMA ============
pdf.secao_titulo('ATORES DO SISTEMA')

pdf.texto_normal('O sistema reconhece cinco atores distintos, cada um com responsabilidades específicas dentro do fluxo de atendimento:', size=8)
pdf.ln(2)

colunas_atores = ['#', 'Ator', 'Perfil', 'Atuação no sistema']
larguras_atores = [8, 40, 30, 189]

pdf.tabela_cabecalho(colunas_atores, larguras_atores)

dados_atores = [
    ['1', 'Recepcionista', 'Recepção', 'Porta de entrada — cadastra o paciente e abre o atendimento'],
    ['2', 'Enfermeiro(a) de Triagem', 'Enfermagem', 'Coleta sinais vitais e classifica o risco do paciente'],
    ['3', 'Médico(a)', 'Médico', 'Realiza a consulta, prescreve e decide o encaminhamento'],
    ['4', 'Equipe Enf. - Sala de Medicação', 'Enfermagem', 'Administra medicamentos, faz procedimentos e decide o desfecho pós-medicação'],
    ['5', 'Enfermeiro(a) de Transferência', 'Enfermagem', 'Organiza e documenta a transferência inter-hospitalar'],
]

for i, linha in enumerate(dados_atores):
    pdf.tabela_linha(linha, larguras_atores, fill=(i % 2 == 0))

pdf.ln(3)
pdf.set_font('Helvetica', 'I', 7)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 4, 'Nota: Os atores 2, 4 e 5 compartilham o mesmo perfil técnico (Enfermagem) no sistema, mas atuam em setores fisicamente distintos do hospital.')
pdf.set_text_color(0, 0, 0)
pdf.ln(2)

# ============ CENÁRIO 1 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 1 — Alta Direta pelo Médico')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('O caso mais simples. O paciente é atendido, avaliado pelo médico e recebe alta sem necessidade de medicação hospitalar.', size=8)
pdf.texto_normal('Exemplo clínico: Consulta de rotina, receita de medicamento domiciliar, orientação ambulatorial.', size=8)
pdf.ln(2)

pdf.desenhar_fluxograma(
    'Sequência: Recepção → Triagem → Médico → ✅ Alta',
    ['Recepção', 'Triagem', 'Médico', '✅ Alta'],
    ['Cadastro/Abertura', 'Sinais Vitais/Risco', 'Consulta/Diagnóstico', 'Alta Médica']
)

pdf.subtitulo('Etapas e responsabilidades')

colunas_etapas = ['Etapa', 'Ator', 'Ação realizada', 'Status gerado']
larguras_etapas = [12, 40, 140, 75]

pdf.tabela_cabecalho(colunas_etapas, larguras_etapas)

etapas_c1 = [
    ['1', 'Recepcionista', 'Busca paciente por CPF (ou cadastra novo); abre o atendimento', 'AGUARDANDO_TRIAGEM'],
    ['2', 'Enf. de Triagem', 'Chama o paciente; coleta PA, temperatura, FC, SpO₂, HGT, peso; registra alergias e queixa principal; define classificação de risco por cor', 'AGUARDANDO_MEDICO'],
    ['3', 'Médico', 'Analisa triagem; realiza consulta; registra diagnóstico, CID e prescrição; seleciona "Dar Alta Médica"', 'ALTA'],
]

for i, linha in enumerate(etapas_c1):
    pdf.tabela_linha(linha, larguras_etapas, fill=(i % 2 == 0))

# ============ CENÁRIO 2 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 2 — Medicação e Alta pela Enfermagem')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('O médico prescreve medicação para ser administrada dentro do hospital. Após a medicação, a equipe de enfermagem libera o paciente diretamente.', size=8)
pdf.texto_normal('Exemplo clínico: Hidratação venosa simples, analgesia IM, antieméticos, nebulização.', size=8)
pdf.ln(2)

pdf.desenhar_fluxograma(
    'Sequência: Recepção → Triagem → Médico → Sala de Medicação → ✅ Alta',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', '✅ Alta'],
    ['Cadastro/Abertura', 'Sinais/Risco', 'Prescrição', 'Administração', 'Liberação']
)

pdf.subtitulo('Etapas e responsabilidades')
pdf.tabela_cabecalho(colunas_etapas, larguras_etapas)

etapas_c2 = [
    ['1', 'Recepcionista', 'Busca paciente por CPF (ou cadastra novo); abre o atendimento', 'AGUARDANDO_TRIAGEM'],
    ['2', 'Enf. de Triagem', 'Triagem completa com sinais vitais e classificação de risco', 'AGUARDANDO_MEDICO'],
    ['3', 'Médico', 'Consulta, diagnóstico e prescrição → seleciona "Enviar p/ Medicação"', 'AGUARDANDO_MEDICACAO'],
    ['4', 'Equipe Sala de Med.', 'Visualiza a prescrição médica; administra medicamentos; marca procedimentos como realizados; registra observações de enfermagem; seleciona "Liberar (Alta)"', 'ALTA'],
]

for i, linha in enumerate(etapas_c2):
    pdf.tabela_linha(linha, larguras_etapas, fill=(i % 2 == 0))

# ============ CENÁRIO 3 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 3 — Medicação, Observação e Alta pela Enfermagem')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('Após a medicação, o paciente fica em observação. A equipe de enfermagem acompanha a evolução e libera o paciente quando adequado.', size=8)
pdf.texto_normal('Exemplo clínico: Crise alérgica leve, crise hipertensiva controlada, dor abdominal sob observação.', size=8)
pdf.ln(2)

pdf.desenhar_fluxograma(
    'Sequência: Recepção → Triagem → Médico → Medicação → Observação (ciclos) → ✅ Alta',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', 'Observação', '✅ Alta'],
    ['Cadastro', 'Sinais/Risco', 'Prescrição', 'Administração', 'Repete se necessário', 'Liberação'],
    setas_duplas=[4]
)

pdf.subtitulo('Etapas e responsabilidades')
pdf.tabela_cabecalho(colunas_etapas, larguras_etapas)

etapas_c3 = [
    ['1', 'Recepcionista', 'Busca paciente por CPF (ou cadastra novo); abre o atendimento', 'AGUARDANDO_TRIAGEM'],
    ['2', 'Enf. de Triagem', 'Triagem completa com sinais vitais e classificação de risco', 'AGUARDANDO_MEDICO'],
    ['3', 'Médico', 'Consulta e prescrição → seleciona "Enviar p/ Medicação"', 'AGUARDANDO_MEDICACAO'],
    ['4', 'Equipe Sala de Med.', 'Administra medicação → seleciona "Manter em Observação"', 'EM_OBSERVACAO'],
    ['5*', 'Equipe Sala de Med.', 'Paciente visível na fila; novos ciclos de medicação registrados; cada ciclo gera registro com data, hora e profissional', 'EM_OBSERVACAO'],
    ['6', 'Equipe Sala de Med.', 'Avalia que o paciente está estável → seleciona "Liberar (Alta)"', 'ALTA'],
]

for i, linha in enumerate(etapas_c3):
    pdf.tabela_linha(linha, larguras_etapas, fill=(i % 2 == 0))

pdf.ln(2)
pdf.set_font('Helvetica', 'I', 7)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 4, '* Etapa repetível. Todo o histórico de observações é acumulado automaticamente com data, hora e nome do profissional.')
pdf.set_text_color(0, 0, 0)

# ============ CENÁRIO 4 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 4 — Medicação, Observação e Retorno ao Médico')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('Após medicação/observação, a equipe de enfermagem entende que o paciente precisa de nova avaliação médica antes da liberação.', size=8)
pdf.texto_normal('Exemplo clínico: Paciente com melhora parcial, evolução clínica incerta, necessidade de revisão do diagnóstico.', size=8)
pdf.ln(2)

pdf.desenhar_fluxograma(
    'Sequência: Recepção → Triagem → Médico → Medicação → Médico (Retorno) → ✅ Alta',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', 'Médico', '✅ Alta'],
    ['Cadastro', 'Sinais/Risco', '1ª Consulta', 'Administração', 'Retorno', 'Alta Médica']
)

pdf.subtitulo('Etapas e responsabilidades')
pdf.tabela_cabecalho(colunas_etapas, larguras_etapas)

etapas_c4 = [
    ['1', 'Recepcionista', 'Busca paciente por CPF (ou cadastra novo); abre o atendimento', 'AGUARDANDO_TRIAGEM'],
    ['2', 'Enf. de Triagem', 'Triagem completa com sinais vitais e classificação de risco', 'AGUARDANDO_MEDICO'],
    ['3', 'Médico', 'Consulta e prescrição → seleciona "Enviar p/ Medicação"', 'AGUARDANDO_MEDICACAO'],
    ['4', 'Equipe Sala de Med.', 'Administra medicação → seleciona "Retornar Médico"', 'AGUARDANDO_RETORNO'],
    ['5', 'Médico', 'Visualiza resumo clínico completo (triagem + prescrição + histórico de observações); reavalia; registra desfecho final → "Conceder Alta Médica"', 'ALTA'],
]

for i, linha in enumerate(etapas_c4):
    pdf.tabela_linha(linha, larguras_etapas, fill=(i % 2 == 0))

# ============ CENÁRIO 5 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 5 — Internação')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('O paciente necessita de internação hospitalar. Esta decisão pode ocorrer em três momentos distintos do fluxo.', size=8)
pdf.texto_normal('Exemplo clínico: Pneumonia grave, descompensação de doença crônica, necessidade de cuidados intensivos.', size=8)
pdf.ln(3)

pdf.subtitulo('Quem pode acionar a Internação e em qual momento')

colunas_int = ['Momento no fluxo', 'Ator', 'Ação no sistema', 'Status']
larguras_int = [55, 45, 130, 37]

pdf.tabela_cabecalho(colunas_int, larguras_int)

internacoes = [
    ['Logo após a consulta inicial', 'Médico', 'Avalia que o caso exige internação imediata → seleciona "Solicitar Internação" na tela de consulta', 'INTERNACAO'],
    ['Após administração de medicação', 'Equipe Sala de Med.', 'Avalia piora ou não resposta ao tratamento → seleciona "Solicitar Internação" na sala de medicação', 'INTERNACAO'],
    ['Após retorno ao médico', 'Médico', 'Reavalia e conclui necessidade de internação → seleciona "Solicitar Internação" na tela de retorno', 'INTERNACAO'],
]

for i, linha in enumerate(internacoes):
    pdf.tabela_linha(linha, larguras_int, fill=(i % 2 == 0))

pdf.ln(3)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(204, 0, 0)
pdf.multi_cell(0, 5, 'IMPORTANTE: A internação encerra o atendimento ambulatorial. O paciente passa a ser acompanhado pelo setor de internação do hospital.')
pdf.set_text_color(0, 0, 0)
pdf.ln(2)

# Mini fluxogramas
pdf.subtitulo('Caminhos para Internação:')

pdf.desenhar_fluxograma(
    'Caminho 1: Internação direta pelo Médico',
    ['Recepção', 'Triagem', 'Médico', '🏥 Internação'],
    ['Cadastro', 'Sinais/Risco', 'Decisão', 'Encerra Ambulatório']
)

pdf.desenhar_fluxograma(
    'Caminho 2: Internação pela Enfermagem após Medicação',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', '🏥 Internação'],
    ['Cadastro', 'Sinais/Risco', 'Prescrição', 'Piora/Não Resposta', 'Encerra Ambulatório']
)

pdf.desenhar_fluxograma(
    'Caminho 3: Internação pelo Médico após Retorno',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', 'Médico', '🏥 Internação'],
    ['Cadastro', 'Sinais/Risco', '1ª Consulta', 'Administração', 'Reavaliação', 'Encerra']
)

# ============ CENÁRIO 6 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 6 — Transferência Inter-Hospitalar')

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('O médico avalia que o hospital não possui recursos suficientes e indica transferência. Um enfermeiro designado preenche o documento de transferência.', size=8)
pdf.texto_normal('Exemplo clínico: Necessidade de UTI, cirurgia de alta complexidade, especialidade indisponível no município.', size=8)
pdf.ln(2)

pdf.desenhar_fluxograma(
    'Sequência: Recepção → Triagem → Médico → Medicação → Médico → Enf. Transf. → 🚑 Transferido',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', 'Médico', 'Enf. Transf.', '🚑 Transf.'],
    ['Cadastro', 'Sinais/Risco', '1ª Consulta', 'Estabilização', 'Indicação', 'Documentação', 'Finalizado']
)

pdf.subtitulo('Etapas e responsabilidades')

colunas_transf = ['Etapa', 'Ator', 'Ação realizada', 'Status gerado']
larguras_transf = [12, 45, 135, 75]

pdf.tabela_cabecalho(colunas_transf, larguras_transf)

etapas_c6 = [
    ['1', 'Recepcionista', 'Busca paciente por CPF (ou cadastra novo); abre o atendimento', 'AGUARDANDO_TRIAGEM'],
    ['2', 'Enf. de Triagem', 'Triagem e classificação de risco', 'AGUARDANDO_MEDICO'],
    ['3', 'Médico', 'Consulta e prescrição (estabilização do paciente) → "Enviar p/ Medicação"', 'AGUARDANDO_MEDICACAO'],
    ['4', 'Equipe Sala de Med.', 'Estabiliza o paciente → seleciona "Retornar Médico"', 'AGUARDANDO_RETORNO'],
    ['5', 'Médico', 'Avalia que o caso excede a capacidade do hospital; registra desfecho final como "Transferência"', 'AGUARDANDO_TRANSFERENCIA'],
    ['6', 'Enf. de Transferência', 'Preenche ficha completa: médico solicitante, enfermeiro responsável, técnicos, motorista, hospital de destino e senha de validação (obtida por ligação com hospital receptor); confirma envio', 'TRANSFERIDO'],
]

for i, linha in enumerate(etapas_c6):
    pdf.tabela_linha(linha, larguras_transf, fill=(i % 2 == 0))

pdf.ln(3)
pdf.set_font('Helvetica', 'B', 8)
pdf.set_text_color(204, 0, 0)
pdf.multi_cell(0, 5, 'IMPORTANTE: O documento de transferência fica registrado no sistema e pode ser consultado e impresso a qualquer momento pelo histórico do atendimento.')
pdf.set_text_color(0, 0, 0)

# ============ CENÁRIO 7 ============
pdf.add_page()
pdf.secao_titulo('CENÁRIO 7 — Óbito', pdf.cor_destaque)

pdf.texto_normal('Descrição:', bold=True)
pdf.texto_normal('O paciente vai a óbito durante o atendimento. O registro pode ser feito em três momentos distintos do fluxo, por profissional habilitado.', size=8)
pdf.ln(3)

pdf.subtitulo('Quem pode registrar o Óbito e em qual momento')

colunas_obito = ['Momento no fluxo', 'Ator', 'Ação no sistema', 'Status']
larguras_obito = [55, 45, 130, 37]

pdf.tabela_cabecalho(colunas_obito, larguras_obito)

obitos = [
    ['Logo após a consulta inicial', 'Médico', 'Constata o óbito → seleciona "Declarar Óbito" na tela de consulta', 'OBITO'],
    ['Durante ou após a medicação', 'Equipe Sala de Med.', 'Constata o óbito durante o procedimento → seleciona "Óbito" na sala de medicação', 'OBITO'],
    ['Após retorno ao médico', 'Médico', 'Constata o óbito na reavaliação → seleciona "Declarar Óbito" na tela de retorno', 'OBITO'],
]

for i, linha in enumerate(obitos):
    pdf.tabela_linha(linha, larguras_obito, fill=(i % 2 == 0))

pdf.ln(3)

# Mini fluxogramas de óbito
pdf.subtitulo('Caminhos para registro de Óbito:')

pdf.desenhar_fluxograma(
    'Caminho 1: Óbito constatado pelo Médico na consulta inicial',
    ['Recepção', 'Triagem', 'Médico', '💀 Óbito'],
    ['Cadastro', 'Sinais/Risco', 'Constatação', 'Registrado']
)

pdf.desenhar_fluxograma(
    'Caminho 2: Óbito durante medicação',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', '💀 Óbito'],
    ['Cadastro', 'Sinais/Risco', 'Prescrição', 'Constatação', 'Registrado']
)

pdf.desenhar_fluxograma(
    'Caminho 3: Óbito constatado no retorno ao Médico',
    ['Recepção', 'Triagem', 'Médico', 'Sala Med.', 'Médico', '💀 Óbito'],
    ['Cadastro', 'Sinais/Risco', '1ª Consulta', 'Administração', 'Constatação', 'Registrado']
)

# ============ VISÃO GERAL ============
pdf.add_page()
pdf.secao_titulo('VISÃO GERAL — Todos os Desfechos Possíveis')

colunas_desfecho = ['Desfecho', 'Status final', 'Pode ser registrado por']
larguras_desfecho = [35, 45, 187]

pdf.tabela_cabecalho(colunas_desfecho, larguras_desfecho)

desfechos = [
    ['✅ Alta', 'ALTA', 'Médico (consulta) · Médico (retorno) · Equipe Sala de Med.'],
    ['🏥 Internação', 'INTERNACAO', 'Médico (consulta) · Médico (retorno) · Equipe Sala de Med.'],
    ['🚑 Transferência', 'TRANSFERIDO', 'Médico indica o desfecho → Enf. de Transferência documenta e confirma'],
    ['💀 Óbito', 'OBITO', 'Médico (consulta) · Médico (retorno) · Equipe Sala de Med.'],
]

for i, linha in enumerate(desfechos):
    pdf.tabela_linha(linha, larguras_desfecho, fill=(i % 2 == 0))

pdf.ln(8)

# ============ RESUMO ============
pdf.secao_titulo('RESUMO — O que cada ator faz')

colunas_resumo = ['Ator', 'Responsabilidades no sistema']
larguras_resumo = [45, 222]

pdf.tabela_cabecalho(colunas_resumo, larguras_resumo)

resumo_atores = [
    ['Recepcionista', 'Buscar paciente por CPF · Cadastrar novo paciente · Abrir atendimento · Enviar para a fila de triagem'],
    ['Enf. de Triagem', 'Coletar sinais vitais (PA, temperatura, FC, SpO₂, HGT, peso) · Registrar alergias · Registrar queixa principal · Definir classificação de risco por cor (Manchester) · Encaminhar para o médico'],
    ['Médico', 'Visualizar fila por prioridade · Consultar dados de triagem · Registrar diagnóstico e CID · Escrever prescrição · Decidir encaminhamento: medicação, alta, internação, óbito ou transferência · Realizar retorno e fechar o atendimento'],
    ['Equipe Sala de Med.', 'Visualizar prescrição médica · Confirmar execução de procedimentos · Registrar observações de enfermagem com carimbo automático (data/hora/profissional) · Decidir sobre observação, retorno ao médico, internação, alta ou óbito'],
    ['Enf. de Transferência', 'Registrar equipe de transporte (enfermeiro, técnicos, motorista) · Informar hospital de destino · Registrar senha de validação obtida com hospital receptor · Finalizar e fechar o atendimento'],
]

for i, linha in enumerate(resumo_atores):
    pdf.tabela_linha(linha, larguras_resumo, fill=(i % 2 == 0))

# Salvar PDF no diretório atual
caminho_arquivo = 'fluxos_atendimento_maria_gercina.pdf'
pdf.output(caminho_arquivo)

print(f"PDF gerado com sucesso em: {os.path.abspath(caminho_arquivo)}")
print(f"Total de páginas: {pdf.page_no()}")