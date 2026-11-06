import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import radar

AGORA = 1_800_000_000
CFG = {**radar.PADROES, "max_por_perfil": 2}


def video(id_, perfil="a", views=100, x=1.0, dias=30):
    return {"id": id_, "perfil": perfil, "views": views, "acima_da_media": x,
            "postado": AGORA - dias * radar.DIA}


class Escolher(unittest.TestCase):
    def test_poucas_comeca_pelo_mais_fraco(self):
        videos = [video("1", x=0.8), video("2", x=0.1), video("3", x=3)]
        self.assertEqual([v["id"] for v in radar.escolher(videos, CFG, "poucas", AGORA)], ["2", "1"])

    def test_poucas_ignora_video_recente(self):
        self.assertEqual(radar.escolher([video("1", x=0.1, dias=3)], CFG, "poucas", AGORA), [])

    def test_muitas_comeca_pelo_mais_forte(self):
        videos = [video("1", x=0.8), video("2", x=9, dias=2)]
        self.assertEqual([v["id"] for v in radar.escolher(videos, CFG, "muitas", AGORA)], ["2", "1"])

    def test_respeita_limite_por_perfil_e_historico(self):
        videos = [video(str(i), x=0.1 * (i + 1)) for i in range(4)]
        ids = [v["id"] for v in radar.escolher(videos, CFG, "poucas", AGORA, {"0"})]
        self.assertEqual(ids, ["1", "2"])


class Numeracao(unittest.TestCase):
    def test_continua_de_onde_parou(self):
        with tempfile.TemporaryDirectory() as temp:
            pasta = Path(temp)
            (pasta / "CV2.mp4").touch()
            (pasta / "CV10.mp4").touch()
            (pasta / "outro.mp4").touch()
            self.assertEqual(radar.proximo_numero(pasta, "CV"), 11)


if __name__ == "__main__":
    unittest.main()
