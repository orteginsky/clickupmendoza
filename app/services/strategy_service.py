# app/services/strategy_service.py
from typing import Dict, Any
from app.services.lead_service import LeadService
from app.services.assignment_service import FIELD_OPTION_LABELS

STRATEGY_FIELD_OPTION_LABELS: Dict[str, Dict[str, str]] = {
    # Open Case type
    "41889f31-5122-4400-8808-33ded3812d37": {
        "05698115-a644-4d8c-82d5-3b27bada753b": "VAWA",
        "dffc49bf-88c5-4170-b0fa-351bec93470d": "VAWA AOS",
        "fe3240ab-15ae-4257-9f41-efecf64c9a21": "VAWA DA",
        "f472b7e0-8ea6-4e5b-94d0-71ab62be14c4": "VISA T",
        "d14dd2b9-25d4-43d2-af49-cfd06a0bd314": "VAWA COR",
        "12403900-8ad4-4f5d-bab4-2d1047c2e414": "T VISA COYOTE",
        "309b3a04-8919-439c-ada1-363e0e6dbcf6": "T VISA LABOR",
        "4ebaa09e-2576-4472-95aa-66dcb4ec1896": "T VISA DOMESTIC VIOLENCE",
        "8d0dc102-2e3d-4a2b-8ddd-b47b020b0d81": "T VISA GENERAL TRAFFIC",
        "a4101619-685d-423f-916f-a4781206ca30": "U CERTIFICATION",
        "de0bf0fd-9c8c-4425-89c8-275d6cf8a898": "U VISA",
        "58428634-9899-4914-ad8f-f94cd80acff2": "K VISA",
        "15c02f76-cf1a-4c8c-90c9-b43965f12b0d": "K1 VISA",
        "7a22cfca-ae8c-4374-876b-d9d69d746382": "K2 VISA",
        "f596bcd4-ce56-4933-9b1c-e3e617a89de7": "K2",
        "31b41265-75c5-4eae-bb73-b05c66aab3a2": "CONSULAR PROCESS",
        "22562305-a716-441f-af10-4be11c19cc79": "I - 601a + i-130",
        "54613eef-2886-4ef5-8a85-a0077bf39f7a": "REG AOS",
        "8f0aa465-2b27-415c-a3dd-f844619e6a06": "PIP",
        "a6bdb3e4-deae-41bc-947a-9353705d9078": "PIP INICIAL",
        "50f065c9-e4ce-4a2a-a030-a5a603ac18cc": "PIP AOS",
        "2cb4ef24-f4ea-4f2b-9f22-00daa7959d26": "DACA",
        "84db34f7-e293-4b42-97da-ca91962a139a": "DACA RENEWAL",
        "96514d7c-3590-431b-82ea-eb1b6684f434": "I-90",
        "03a3a7af-511f-4e67-b8f5-13046fd3df87": "I-485",
        "78542c3b-a730-4c5e-a72a-36d809bc9e96": "I-130",
        "e4b1205d-512e-4a53-aeb8-e8d763258b88": "I-601",
        "39deed69-df33-4356-b809-48c5aee65cfd": "I-601A",
        "77b10c11-4cad-4f74-a335-bfe40256df49": "I-751",
        "9087b2a9-6761-498a-991d-328ecc5a5052": "245i",
        "f9f60280-2f25-4cf6-b8d3-04cbfc7be8ee": "AOS 245i",
        "105b0a3f-6f08-4761-a349-423f407a0640": "N-400",
        "e150e441-edae-41e4-b30f-3951ab58c8c6": "N-600",
        "8b025b71-4428-4736-9226-ba3abba68276": "Derivate",
        "a1d13628-0fd7-4318-a464-ae2e0ac8892a": "FOIA",
        "202925b7-7b16-43d4-8df8-23402eba30d2": "CBP FOIA",
        "029ecf10-59c0-4efc-9e1f-b0af423823e6": "FBI FOIA",
        "bbf75194-9479-4072-8d24-07b9aec3adc5": "USCIS FOIA",
        "95574544-1e2b-4b35-97fc-3df0e4ac2c09": "ICE FOIA",
        "7805cb31-0f8e-4c75-8e66-5ea03588c436": "EAD RENEWAL",
        "1a5c377e-12b3-4651-ba16-046f2226f190": "EAD Correction",
        "6eb7cb05-5d47-4899-af72-3d7742deb021": "VAWA - Rejection",
        "81992b82-0af2-46a0-ab99-f074a4cda417": "VISA T - Rejection",
        "087126e3-ec65-4583-9a11-1b3808e7ef15": "AOS - Rejection",
        "5576ee7a-b350-4ab5-9be4-d150f99f812d": "USCIS DECISION",
        "57325cbd-eebc-4359-9caf-e8feb680443e": "PC",
        "69a62965-1122-418c-87a9-0c9ffba80813": "REACTIVACION",
        "5a9ef7ce-fb54-4666-b5de-67571d8cb2f3": "PI",
        "2df349ed-2459-4a62-9560-fa1f3c320555": "open",
        "d5c61c17-bb45-4b53-8c74-9e92c5f574cc": "In Progress",
        "247eed8c-2fe4-46bc-a2e2-2945f3263e64": "Initial Investigation",
        "c62e4062-ba0b-4582-aaeb-6673c36793fe": "REMOVALS",
        "73f59492-1b61-420d-9e82-6440f84f1b17": "COURT FOIA",
        "b2b58620-11ee-490a-b08e-3980e83024d2": "CLOSED",
        "76c5c416-6a05-46fb-91cb-1516ba6cf86c": "AOS 245A",
        "74a0b3fb-a53e-4bf4-82e6-8d8793aa62b5": "NATZ",
        "ade229b1-c85c-4c9c-a370-15a7915c7fa1": "Non-contact letter sent",
        "cb7c9f93-41f3-4a2a-87fd-b3e8bd040edc": "PIP MILITARY",
        "db70db6e-a51e-4226-b55c-3a3ea5fa1475": "LPR Renewal",
        "2174e4b0-abf9-494c-8886-8230363ae30d": "T VISA LA",
        "5d990700-6f4a-45f6-b070-aa9cc28db358": "VAWA + 751",
        "723cd240-7f65-4b6d-a9b9-0af9ca1da703": "Removal defense",
        "c00b620f-9f6f-4e4f-a40a-c937eb903685": "PIP DA",
        "7c1157dd-1b06-4d60-9be2-c64818f91ae1": "Obtención de reporte policial",
        "d5836a71-9d3d-4338-ab62-3e3fc1f65368": "No encontrado",
        "a4e67e2e-9e3b-4846-91c9-79dad37e2689": "i -212 + i-130",
        "b5f2b1cc-b2c0-4ccf-bf40-55dbf6f3eeec": "I-765 Initial Application",
        "2d201404-c405-48de-9242-70d83c3aa9d6": "AOS AFTER VISA K1",
        "9108075f-3754-4353-b172-a9abe5976253": "he says that if we do not offer a solution soon he will sue us for not complying with what was agreed.",
        "f488d8f6-5e24-40a0-9c22-22c96e4d6e89": "she says that her case does not move forward she threatens to take legal action if we dont give her any solution asap.",
        "fe3677ba-ea5c-4857-8cc4-0ef634953739": "I-130 + I-485",
        "7a3d4954-d0dc-4698-92c0-5326c4668d89": "COURT",
        "938a099b-8f38-41da-b8c9-7cc3839cb41d": "i751 VAWA"
    },
    # CASO
    "915294ac-d1a1-4545-8429-72ca9002c234": {
        "50a90a2b-9730-412c-8b96-43b8cdad6bec": "COMBO",
        "4a0cc4f1-1660-4e98-948f-4a49af8370b8": "DERIVADO",
        "608e7b0d-e099-4049-9aed-ccd5ba18b04b": "INDIVIDUAL"
    },
    # Attorney LSU/CB
    "f18ca98e-67b0-4f93-8dc3-a863d6c7cb8d": {
        "97853759-d0f8-4da0-8ec2-0cecc8d4ae73": "Aaron Dickey",
        "94359d26-43d0-40d2-b2ed-9ff2a722a43f": "Albalis Rodriguez",
        "764bb25d-4f22-4c3b-a58e-d570a74d8826": "Barbara Becerra",
        "eb1b69f8-288f-4c53-b23a-3979c23f1e9c": "Betzaida Santiago",
        "36127378-c318-4bce-b8f9-b823383087af": "Cesar Meraz",
        "019e7c1a-5989-4658-96a1-4a4e416ca5a3": "Cristian Soto",
        "1276ab9e-8f49-42b0-b0ea-60a546036f16": "Daniel Patiño",
        "35a2eb94-6de8-46de-a24f-a24330621504": "Erick Dessus",
        "41f3f2ff-759d-48c8-962f-0aa04dcf53d9": "Felmarie Figueroa",
        "db3b03cf-f730-4b36-80b9-6c4bf3c0835e": "Jesus Martinez",
        "d792f9da-831f-4e2a-af26-9bebc512e775": "Jeyka Perez",
        "be8f241c-7617-4255-b135-5dc0e0a5d835": "Laura Rivera",
        "3ab4e6bd-6810-435a-920b-006537f409bd": "Luis Tirado",
        "1130ab2b-f705-487c-98a7-25a8bf1362bf": "María Mendoza",
        "3a556da8-8ca5-45ba-a96b-7c97de9e3713": "Melissa Aviles",
        "2df0ac0b-cb76-463a-833f-738f7f15dfcb": "Paola Linares",
        "4944f24e-5207-4c9f-82e1-cfc9d169693b": "Paola Rodriguez",
        "88629519-27b4-48f9-9a44-7ec47d7170d9": "Saquia Rivera",
        "7dda6f51-2acf-4c81-9e76-f3081b3355e0": "Vanelisse Encarnación",
        "bbf2076f-cb40-416e-8980-941e22148cac": "Yanira Gordils",
        "be56328a-56af-4898-922e-98e7811abbd6": "Yiriann Perez"
    }
}

class StrategyService:
    ID_MAP = {
        "7609ea7c-eea0-4944-a6fa-22cedde72b14": "id_cliente",
        "915294ac-d1a1-4545-8429-72ca9002c234": "caso",
        "d4fe1b9e-bf4b-4883-b64f-d9020bfd89af": "fecha_de_venta",
        "0e06e00d-2d08-4cb1-a662-66c390de105d": "fecha_consulta_original",
        "87b3bd44-10fa-4499-8571-0af9d4891987": "phone",
        "f18ca98e-67b0-4f93-8dc3-a863d6c7cb8d": "attorney_lsucb",
        "b1a419d5-6ba2-4d14-826f-530c1378442f": "fecha_de_asignacin",
        "54128015-de28-4d43-a4c7-a635a2fc7dbd": "paralegal_report",
        "ac2aeda6-0f95-414b-9f4d-309d3a2c7793": "link_de_rs",
        "8e4639dc-b459-40ca-88ae-075b8146d440": "link_tramcase",
        "41889f31-5122-4400-8808-33ded3812d37": "open_case_type"
    }

    @staticmethod
    def transform_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma el JSON de ClickUp al formato de nuestra DB."""
        
        # 1. Campos de Sistema
        result = {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "status": task_data.get("status", {}).get("status"),
            "priority": task_data.get("priority", {}).get("priority") if task_data.get("priority") else None,
            "date_created": LeadService._parse_clickup_date(task_data.get("date_created")),
        }

        # Procesar Asignados
        assignees = task_data.get("assignees", [])
        result["assignee"] = ", ".join(
            filter(None, [a.get("username") or a.get("email", "") for a in assignees])
        ) or None
            
        # 2. Procesar Custom Fields por ID
        custom_fields = task_data.get("custom_fields", [])
        for field in custom_fields:
            f_id = field.get("id")
            if f_id in StrategyService.ID_MAP:
                col_name = StrategyService.ID_MAP[f_id]
                val = field.get("value")
                
                # Lógica de casteo según tipo de ClickUp
                f_type = field.get("type")
                if f_type == "date" and val:
                    result[col_name] = LeadService._parse_clickup_date(val)
                elif f_type == "checkbox":
                    result[col_name] = val is True or val == "true"
                elif f_type in ("drop_down", "labels"):
                    # Priorizar mapa de estrategia, caer a mapa general si no existe
                    option_map = STRATEGY_FIELD_OPTION_LABELS.get(f_id)
                    if option_map is None:
                        option_map = FIELD_OPTION_LABELS.get(f_id, {})
                        
                    if isinstance(val, list):
                        result[col_name] = ", ".join(
                            option_map.get(str(v), str(v)) for v in val if v
                        )
                    elif val is not None:
                        result[col_name] = option_map.get(str(val), str(val))
                    else:
                        result[col_name] = None
                else:
                    result[col_name] = val

        return result
