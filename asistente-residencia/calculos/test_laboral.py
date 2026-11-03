import unittest
from datetime import date

from laboral import (
    aviso_previo,
    anos_indemnizables,
    anos_servicio,
    indemnizacion_anos_servicio,
)


class TestAntiguedad(unittest.TestCase):
    def test_anos_y_meses(self):
        self.assertEqual(anos_servicio(date(2020, 3, 15), date(2024, 5, 20)), (4, 2))

    def test_dia_no_cumplido_resta_mes(self):
        self.assertEqual(anos_servicio(date(2020, 3, 15), date(2024, 3, 10)), (3, 11))

    def test_termino_antes_de_ingreso(self):
        with self.assertRaises(ValueError):
            anos_servicio(date(2024, 1, 1), date(2023, 1, 1))


class TestIndemnizacion(unittest.TestCase):
    def test_fraccion_mayor_a_seis_meses_suma_un_ano(self):
        self.assertEqual(anos_indemnizables(3, 7), 4)

    def test_fraccion_de_seis_meses_no_suma(self):
        self.assertEqual(anos_indemnizables(3, 6), 3)

    def test_tope_de_once_anos(self):
        self.assertEqual(anos_indemnizables(15, 0), 11)

    def test_monto_con_tope_de_remuneracion(self):
        monto = indemnizacion_anos_servicio(
            date(2015, 1, 1), date(2020, 1, 1), 1_000_000, tope_remuneracion=800_000
        )
        self.assertEqual(monto, 5 * 800_000)


class TestAvisoPrevio(unittest.TestCase):
    def test_sin_aviso_paga_treinta_dias(self):
        self.assertEqual(aviso_previo(900_000), 900_000)

    def test_con_aviso_parcial(self):
        self.assertEqual(aviso_previo(900_000, dias_avisados=15), 450_000)


if __name__ == "__main__":
    unittest.main()
