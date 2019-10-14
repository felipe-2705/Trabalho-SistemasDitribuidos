# Trabalho-SistemasDitribuidos


Servidor:

- Requisitos Funcionais:

-> Aceitar conexoes de Clientes;
-> Receber mensagens dos diversos clientes e Salva-las;
-> Enviar as mensagens de um Cliente para os demais;
-> Criar Salas com nome e password;
-> Buscar Salas dado o nome;
-> Para as Salas atribuir um nickname, garantir que nao seja repetido, para cada cliente;
-> Para um Enviar o historico de mensagens antigas;

- Requisitos Não-Funcionais:
-> conseguir ouvir mensagens , enviar e aceitar conexoes concorrentemente;
-> Marcar Nickname do cliente que a enviou de cada mensagem;
-> Salvar os historicos de mensagens assim como dados de Salas de modo persistente;

Cliente:

- Requisitos Funcionais:

-> Conectar com um servidor de mensagens;
-> Solicitar ao servidor a criacao de um Sala informando nome e senha;
-> Informar ao servidor do nickname dado pelo usuario;
-> Solicitar ao servidor acesso a uma sala aberta;
-> Enviar mensagens ao Servidor;
-> Receber mensagens do Servidor;
-> Dispor as Mensagens no display grafico com Nickname do Cliente que enviou;

- Requisitos Não-Funcionais:

-> Receber e enviar mensagens de maneira concorrente;

Mensagens{
     'nickname':'nome',
     'mensagem': 'Texto'       
}
