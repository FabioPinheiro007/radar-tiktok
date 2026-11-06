#!/usr/bin/env python3
"""Radar TikTok: acha vídeos de concorrentes, baixa, limpa metadados e organiza em pastas."""
import argparse
import csv
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
MB = 1024 * 1024
ESPACO_MINIMO = 1024 * MB
TAMANHO_ESTIMADO = 40 * MB
DIA = 86400
PASTAS = {"poucas": "poucas_views", "muitas": "muitas_views"}

PADROES = {
    "perfis": [],
    "modo": "poucas",
    "qtd_videos": 30,
    "dias": 180,
    "idade_minima_poucas": 14,
    "videos_por_perfil": 40,
    "max_por_perfil": 6,
    "prefixo": "CV",
    "marcar_samsung": False,
}


def rodar_pool(funcao, itens, trabalhadores):
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        return list(pool.map(funcao, itens))


def listar_perfil(perfil, limite):
    nome = perfil.strip().lstrip("@")
    if not re.fullmatch(r"[\w.]+", nome):
        print(f"  ! perfil inválido: {perfil}")
        return []
    comando = ["yt-dlp", "--flat-playlist", "-J", "--playlist-end", str(limite),
               f"https://www.tiktok.com/@{nome}"]
    dados, motivo = None, ""
    for tentativa in range(3):
        if tentativa:
            time.sleep(15 * tentativa)
        try:
            saida = subprocess.run(comando, capture_output=True, text=True, timeout=90)
            dados = json.loads(saida.stdout)
            motivo = " ".join(saida.stderr.strip().splitlines()[-1:])
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            motivo = "sem resposta"
        if dados:
            break
    if not dados:
        print(f"  ! não consegui ler @{nome}: {motivo[:120]}")
        return []
    vistos = [v for v in dados.get("entries") or [] if v.get("view_count") is not None]
    if not vistos:
        print(f"  ! @{nome} não trouxe vídeos")
        return []
    mediana = statistics.median(v["view_count"] for v in vistos) or 1
    return [{
        "id": v["id"],
        "perfil": nome,
        "url": v["url"],
        "views": v["view_count"],
        "postado": v.get("timestamp") or 0,
        "acima_da_media": round(v["view_count"] / mediana, 2),
    } for v in vistos]


def escolher(videos, cfg, modo, agora, ja_baixados=()):
    limite = agora - cfg["dias"] * DIA
    candidatos = [v for v in videos if v["id"] not in ja_baixados and v["postado"] >= limite]
    if modo == "poucas":
        # Vídeo novo ainda está ganhando views, então só entra quem já teve tempo de rodar
        idade = agora - cfg["idade_minima_poucas"] * DIA
        candidatos = [v for v in candidatos if v["postado"] <= idade and v["acima_da_media"] < 1]
        candidatos.sort(key=lambda v: (v["acima_da_media"], v["views"]))
    else:
        candidatos.sort(key=lambda v: (v["acima_da_media"], v["views"]), reverse=True)
    por_perfil, escolhidos = {}, []
    for video in candidatos:
        if por_perfil.get(video["perfil"], 0) < cfg["max_por_perfil"]:
            por_perfil[video["perfil"]] = por_perfil.get(video["perfil"], 0) + 1
            escolhidos.append(video)
    return escolhidos


def duracao(arquivo):
    saida = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "format=duration:stream=codec_type",
                            "-of", "json", str(arquivo)], capture_output=True, text=True)
    try:
        dados = json.loads(saida.stdout)
        return float(dados["format"]["duration"]) if dados.get("streams") else None
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def baixar(video, temp):
    base = temp / video["id"]
    comando = ["yt-dlp", "-q", "--no-warnings", "--no-playlist", "--retries", "3",
               "-f", "bv*+ba/b", "-S", "res,br", "--merge-output-format", "mp4",
               "--max-filesize", "300M", "-o", f"{base}.%(ext)s", video["url"]]
    try:
        subprocess.run(comando, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None
    arquivo = temp / f"{video['id']}.mp4"
    # Post de fotos vem só com áudio e não serve como vídeo
    if arquivo.exists() and duracao(arquivo):
        return {**video, "bruto": arquivo}
    return None


def limpar_metadados(origem, destino, marcar_samsung):
    comando = ["ffmpeg", "-y", "-v", "error", "-i", str(origem),
               "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
               "-map_metadata", "-1", "-map_metadata:s", "-1", "-map_chapters", "-1",
               "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]
    if marcar_samsung:
        comando += ["-metadata", "com.android.manufacturer=samsung",
                    "-metadata", "com.android.model=SM-S921B",
                    "-movflags", "use_metadata_tags+faststart"]
    else:
        comando += ["-movflags", "+faststart"]
    feito = subprocess.run(comando + [str(destino)], capture_output=True)
    antes, depois = duracao(origem), duracao(destino)
    return feito.returncode == 0 and antes and depois and abs(antes - depois) < 0.5


def proximo_numero(pasta, prefixo):
    usados = [int(m[1]) for p in pasta.glob(f"{prefixo}*.mp4")
              for m in [re.fullmatch(rf"{re.escape(prefixo)}(\d+)\.mp4", p.name)] if m]
    return max(usados, default=0) + 1


def baixar_grupo(candidatos, qtd, temp):
    baixados, fila = [], list(candidatos)
    while fila and len(baixados) < qtd:
        lote = fila[:qtd - len(baixados)]
        del fila[:len(lote)]
        livre = shutil.disk_usage(temp).free
        if livre - len(lote) * TAMANHO_ESTIMADO < ESPACO_MINIMO:
            print(f"  ! pouco espaço em disco ({livre // MB} MB livres): parei o download")
            break
        baixados += [v for v in rodar_pool(lambda v: baixar(v, temp), lote, 3) if v]
        print(f"  {len(baixados)}/{qtd} baixados")
    return baixados


def organizar(videos, pasta, cfg, mapa):
    pasta.mkdir(parents=True, exist_ok=True)
    numero = proximo_numero(pasta, cfg["prefixo"])
    linhas = []
    for video in videos:
        nome = f"{cfg['prefixo']}{numero}.mp4"
        if limpar_metadados(video["bruto"], pasta / nome, cfg["marcar_samsung"]):
            linhas.append([pasta.name, nome, video["perfil"], video["views"],
                           video["acima_da_media"], video["url"]])
            numero += 1
        else:
            (pasta / nome).unlink(missing_ok=True)
            print(f"  ! não consegui limpar {video['url']}")
    novo = not mapa.exists()
    with mapa.open("a", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        if novo:
            escritor.writerow(["pasta", "arquivo", "perfil", "views", "x_mediana", "link"])
        escritor.writerows(linhas)
    return len(linhas)


def main():
    parser = argparse.ArgumentParser(description="Radar de vídeos do TikTok")
    parser.add_argument("--config", default=str(BASE / "config.json"))
    parser.add_argument("--saida", default=str(BASE / "videos"))
    parser.add_argument("--qtd", type=int, help="quantos vídeos baixar no total")
    parser.add_argument("--modo", choices=["poucas", "muitas", "ambos"])
    parser.add_argument("--perfis", help="lista separada por vírgula; substitui a do config")
    args = parser.parse_args()

    for programa in ("yt-dlp", "ffmpeg", "ffprobe"):
        if not shutil.which(programa):
            sys.exit(f"Falta instalar: {programa}")
    arquivo = Path(args.config)
    cfg = {**PADROES, **(json.loads(arquivo.read_text()) if arquivo.exists() else {})}
    perfis = args.perfis.split(",") if args.perfis else cfg["perfis"]
    perfis = [p for p in perfis if p.strip()]
    if not perfis:
        sys.exit("Coloque os perfis dos concorrentes em config.json ou use --perfis")
    modo = args.modo or cfg["modo"]
    qtd = args.qtd or cfg["qtd_videos"]

    raiz = Path(args.saida)
    dia = raiz / f"{date.today():%Y-%m-%d}"
    temp = raiz / "_baixando"
    temp.mkdir(parents=True, exist_ok=True)
    historico_arquivo = raiz / "historico.json"
    historico = set(json.loads(historico_arquivo.read_text())) if historico_arquivo.exists() else set()

    inicio = time.time()
    print(f"Lendo {len(perfis)} perfis...")
    listas = rodar_pool(lambda p: listar_perfil(p, cfg["videos_por_perfil"]), perfis, 2)
    videos = [v for lista in listas for v in lista]

    modos = ["poucas", "muitas"] if modo == "ambos" else [modo]
    cotas = [qtd - qtd // 2, qtd // 2] if modo == "ambos" else [qtd]
    total = 0
    usados = set(historico)
    try:
        for grupo, cota in zip(modos, cotas):
            candidatos = escolher(videos, cfg, grupo, time.time(), usados)
            print(f"{PASTAS[grupo]}: {len(candidatos)} candidatos, baixando até {cota}...")
            baixados = baixar_grupo(candidatos, cota, temp)
            feitos = organizar(baixados, dia / PASTAS[grupo], cfg, dia / "mapa.csv")
            total += feitos
            usados |= {v["id"] for v in baixados}
            if feitos < cota:
                print(f"  ! só consegui {feitos} de {cota}. Adicione perfis ou aumente 'dias' no config.json")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
        historico_arquivo.write_text(json.dumps(sorted(usados)))

    print(f"\nPronto: {total} vídeos em {time.time() - inicio:.0f}s")
    print(f"Pasta: {dia}")


if __name__ == "__main__":
    main()
