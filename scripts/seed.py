import sqlite3

def popular_banco_completo():
    conn = sqlite3.connect('oficina.db')
    cursor = conn.cursor()

    # 1. Lista de 10 Clientes (Toledo e arredores)
    clientes = [
        ('João Silva', '123.456.789-00', 'Rua das Flores, 10', 'Toledo', '(45) 99999-1111', 'ABC-1234'),
        ('Maria Oliveira', '987.654.321-11', 'Av. Brasil, 500', 'Toledo', '(45) 98888-2222', 'XYZ-5678'),
        ('Carlos Souza', '444.555.666-77', 'Rua Santos Dumont, 123', 'Cascavel', '(45) 97777-3333', 'KML-9090'),
        ('Ana Beatriz', '111.222.333-44', 'Rua Paraná, 88', 'Toledo', '(45) 99111-4444', 'BRA-2E19'),
        ('Marcos Pontes', '555.444.333-22', 'Rua XV de Novembro, 202', 'Ouro Verde', '(45) 99222-5555', 'JHT-4455'),
        ('Fernanda Lima', '666.777.888-99', 'Av. Parigot, 1500', 'Toledo', '(45) 99333-6666', 'OWP-1020'),
        ('Ricardo Alves', '222.333.444-55', 'Rua General Estilac, 45', 'Toledo', '(45) 99444-7777', 'QWE-9988'),
        ('Patrícia Meira', '333.444.555-66', 'Rua Almirante Barroso, 90', 'Cascavel', '(45) 99555-8888', 'MKP-3321'),
        ('Lucas Gabriel', '777.888.999-00', 'Rua Sete de Setembro, 300', 'São Pedro', '(45) 99666-9999', 'LUI-0011'),
        ('Sonia Abrão', '888.999.000-11', 'Loteamento Biopark', 'Toledo', '(45) 99777-0000', 'BIO-2024')
    ]
    
    cursor.executemany('''
        INSERT INTO clientes (nome, cpf, endereco, cidade, telefone, placa) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', clientes)

    # 2. Lista de 10+ Serviços vinculados aos IDs (1 a 10)
    # Formato: (cliente_id, data, placa, servico, total_saldo, valor_pago, comentario)
    servicos = [
        (1, '2026-03-01', 'ABC-1234', 'Troca de Óleo', 250.0, 250.0, 'Ok.'),
        (2, '2026-03-02', 'XYZ-5678', 'Pneus novos', 1200.0, 1200.0, 'Pago à vista.'),
        (3, '2026-03-03', 'KML-9090', 'Freios Traseiros', 450.0, 0.0, 'Aguardando PIX.'),
        (4, '2026-03-05', 'BRA-2E19', 'Revisão 50k km', 850.0, 425.0, 'Metade paga.'),
        (5, '2026-03-06', 'JHT-4455', 'Bateria Nova', 380.0, 380.0, 'Garantia 1 ano.'),
        (6, '2026-03-08', 'OWP-1020', 'Alinhamento', 150.0, 150.0, 'Sem observações.'),
        (7, '2026-03-10', 'QWE-9988', 'Lâmpada Farol', 45.0, 45.0, 'Substituição rápida.'),
        (8, '2026-03-11', 'MKP-3321', 'Embreagem', 1800.0, 1000.0, 'Saldo para o dia 20.'),
        (9, '2026-03-12', 'LUI-0011', 'Limpeza Radiador', 220.0, 220.0, 'Ok.'),
        (10, '2026-03-13', 'BIO-2024', 'Filtro Ar Condicionado', 110.0, 0.0, 'Pendente.'),
        (1, '2026-03-13', 'ABC-1234', 'Escapamento', 350.0, 350.0, 'Segunda visita do mês.')
    ]

    cursor.executemany('''
        INSERT INTO servicos (cliente_id, data, placa, servico, saldo, pago, comentario) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', servicos)

    conn.commit()
    conn.close()
    print(f"Sucesso! 10 clientes e {len(servicos)} serviços inseridos.")

# Executar a inserção
popular_banco_completo()