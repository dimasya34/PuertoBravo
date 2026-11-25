"""1.7.6, aviso del foro: marcas en el GPS un vehículo tuyo desde el móvil, pides que te lo traigan, te subes, y el
piloto del GPS arranca solo hacia donde estaba antes el vehículo.

El móvil marcaba el sitio, no el vehículo: el destino se quedaba donde lo habías dejado y no se acababa al subir. Ahora
marca el vehículo, como Mayúsculas L: al traértelo, el destino pasa a donde lo dejan, y al subir se acaba. Si ibas a la
casa de su garaje o a su localidad, el destino se quita al traértelo.
"""
import pygame

from juego.menus import Menu


def _elegir(robot, empieza):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(empieza))
    robot.tecla(pygame.K_RETURN)


def _lejos_de(p, v, metros=300.0):
    m = p.mundo
    x = v.x + metros if v.x + metros < m.ancho - 20 else v.x - metros
    p.teletransportar(x, v.y)


def test_marcado_desde_el_movil_y_traido_el_piloto_no_arranca(robot):
    p = robot.nueva_partida()
    v = p.crear_vehiculo("sedan", p.j.x + 6, p.j.y, 1, None, "Brisa de prueba")
    assert p.hacer_mio(v)
    _lejos_de(p, v)
    p.cancelar_gps()                                          # sin la primera misión marcada: el coche sería un desvío de ella
    antes = (v.x, v.y)
    robot.tecla(pygame.K_m)
    _elegir(robot, "Mis vehículos")
    _elegir(robot, "Brisa de prueba")
    _elegir(robot, "Marcarlo en el GPS")
    assert p.gps and p.gps.get("cosa") is v
    p.j.dinero = 1000
    assert p.traer_mi_vehiculo(v) is v
    assert (v.x, v.y) != antes and abs(p.gps["dest"][0] - v.x) < 1 and abs(p.gps["dest"][1] - v.y) < 1    # va adonde lo dejan
    p.cfg["piloto_gps"] = True
    p.cfg["conduccion"] = "asistida"                          # la del jugador: con ella, el piloto conduce solo
    p._subir(v, False, callar=True)
    robot.frames(5)
    assert p.j.veh is v and p.gps is None and not p.piloto_completo()                # al subir se acaba: nada que conducir
    assert "Ya estás en Brisa de prueba" in robot.dicho()


def test_si_ibas_a_su_garaje_y_te_lo_traen_el_gps_se_quita(robot):
    p = robot.nueva_partida()
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)) > 0)
    p.j.propiedades.append(casa.id)
    ficha = {"modelo": "sedan", "salud": 100.0, "nombre": "Furgón de prueba", "mejoras": {}}
    p.j.garajes.setdefault(casa.id, []).append(ficha)
    p.gps_a_lugar(casa)
    p.gps["para"] = ficha                                    # lo que hace «Marcar en el GPS la casa donde está»
    p.j.dinero = 1000
    v = p.traer_mi_vehiculo(ficha, casa.id)
    assert v is not None and p.gps is None and "El GPS se queda sin destino" in robot.dicho()


def test_traido_sin_gps_hacia_el_no_toca_otro_destino(robot):
    p = robot.nueva_partida()
    v = p.crear_vehiculo("sedan", p.j.x + 6, p.j.y, 1, None, "Otro de prueba")
    assert p.hacer_mio(v)
    _lejos_de(p, v)
    l = next(iter(p.mundo.lugares.values()))
    p.gps_a_lugar(l)
    p.j.dinero = 1000
    assert p.traer_mi_vehiculo(v) is v
    assert p.gps is not None and p.gps["nombre"] == l.nombre                          # lo que marcaste para otra cosa sigue


def test_con_una_mision_marcada_al_subir_vuelve_a_ella_y_no_al_sitio_de_antes(robot):
    p = robot.nueva_partida()
    mision = p.gps["nombre"]                                  # la primera misión viene marcada
    v = p.crear_vehiculo("sedan", p.j.x + 6, p.j.y, 1, None, "Brisa de prueba")
    assert p.hacer_mio(v)
    _lejos_de(p, v)
    antes = (v.x, v.y)
    robot.tecla(pygame.K_m)
    _elegir(robot, "Mis vehículos")
    _elegir(robot, "Brisa de prueba")
    _elegir(robot, "Marcarlo en el GPS")
    assert p.gps.get("cosa") is v and p.gps["anterior"]["nombre"] == mision
    p.j.dinero = 1000
    assert p.traer_mi_vehiculo(v) is v
    p._subir(v, False, callar=True)
    robot.frames(5)
    assert p.gps["nombre"] == mision and p.gps["dest"] != antes and "El GPS vuelve a" in robot.dicho()
