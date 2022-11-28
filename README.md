# AlgoTradingPy

AlgoTradingPy é uma biblioteca para backtesting e estratégias de negociação de criptomoeda.


Construindo o pacote:
   
    python3 setup.py sdist bdist_wheel
    
Instalando e executando no Linux
    
    pip3 install --user dist/algotradingpy-1.0.3.tar.gz 
    python -m algotradingpy


Instalando e executando no Windows
    
    python -m pip install --user .\dist\algotradingpy-1.0.3.tar.gz  
    python -m algotradingpy


Como usar no terminal

    python -m algotradingpy [-h] [--config arquivo] [--enable-logging] [--log-dir caminho] [--version]
    argumentos opicionais:
      -h, --help         mostra essa mensagem de ajdua e sai
      --config arquivo   Arquivo de configuração gravável (json). Usado para armazenar parâmetros do banco de dados e símbolos a serem coletados. Padrão:
                         /home/daniel/.AlgoTradingPy/config.json
      --get-data         Coleta e popula continuamente cotações da Bitfinex no banco de dados.
                         Edite o arquivo de configuração (config.json) para incluir ou remover os símbolos,
      --enable-logging   Habilita geração de registros de atividades em arquivo de log. Diretório do arquivo de log pode ser alterado através do argumento --log-dir.
      --log-dir caminho  O diretório onde a saída de registro é salva, precisa terminar com uma barra. Padrão: /home/daniel/.AlgoTradingPy/
      --version          Imprime p número da versão e sai.

    Exemplo: python -m algotradingpy --get-data --config "./config.json" --log-dir "./" --enable-logging


