# app/services/assignment_service.py
from typing import Dict, Any
from app.services.lead_service import LeadService

# Mapa de opciones para campos Drop Down y Labels de la lista 901407053200.
# Estructura: { field_uuid: { option_uuid: label_valor } }
FIELD_OPTION_LABELS: Dict[str, Dict[str, str]] = {
    # 🧑‍⚖️ Abogado Asignado
    "298c4ec5-05e3-432e-82da-cc973c44be54": {
        "3a042ce4-de63-4f8a-b317-321aa54490f9": "Barbara Becerra",
        "e983726e-dbc5-42cc-a00c-e4c04dc63fec": "Cesar Meraz",
        "a4eb05df-8254-4879-8cd0-9c259f86a495": "Cristian Soto",
        "12d71f1c-c2b3-4924-bf63-aba58fe4e707": "Edwin Rivera",
        "573d455e-9de1-41d8-bf07-8040222062ed": "Eric Dessus",
        "71528c49-e4db-4a24-ab24-34b40d47454d": "Felmarie Figueroa",
        "f1ea6143-4258-4573-bfe3-6af24b6621ee": "Jesús Martinez",
        "b85d16ca-513e-4a8e-9edc-243658b363ff": "Jeyka Perez",
        "b2fe74eb-81ae-42e5-9701-67ffded3fd2e": "Laura Rivera",
        "c1aec65e-a25d-4d33-a06a-b9a7708e3434": "Luis Tirado",
        "c55942a4-cbd7-4eba-ae93-15bb87d45e8f": "Melissa Aviles",
        "88db444c-b47f-44f5-a23c-66a96a6f2acf": "Paola Linares",
        "cfdbc68b-6d59-4e63-a486-465a05c878e6": "Paola Rodríguez",
        "dccc72e0-2b1d-481b-b288-1f156d138c96": "Saquia Rivera",
        "a4a64b7f-4d43-4942-9cb9-50c5359cdb9d": "Vanelisse Encarnación",
    },
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
    },
    # Rapsheet
    "6301c50f-5047-4276-98d3-526d5c6b43ea": {
        "6cc09bda-d90d-4ddf-ba7e-4ab61b8d9391": "Si- Trabajable (Legible/Vigente)",
        "85d84f3f-bd8b-4ca6-ae82-578278e89941": "Si- No trabajable (Ilegible/Vencido)",
        "7ad7c31a-1ecb-4012-9eb4-21f3a136515c": "No - Ya se solicito",
        "b0ac7050-d9ba-4a6a-8530-a2efc18b5c43": "No - No se han solicitado",
        "b056b0d8-5b70-4eeb-b642-5512393a0d32": "N/A",
    },
    # 🗂️ Proyecto
    "a1c9d406-838f-48c6-b92c-a25992494b62": {
        "406af472-185b-475a-ba7d-dfd55e90a851": "* Decision",
        "5c4eaa68-d734-497c-b54a-aaf5d9e77b9c": "* Special Process",
        "95073e29-5917-448d-ab5f-869c16cf287f": "2018-2022",
        "fe3d4b33-285f-448e-b1ca-2d99c6486b0d": "9825",
        "012511fa-73d0-4b32-9f89-cb17042250da": "Backlog Q1 y Q2",
        "e43898e5-c7c3-44a5-b190-f994db0972be": "Backlog Q3,Q4",
        "87dc3ab9-8cd5-47b3-a7f7-a99410bced7a": "Consular Process",
        "95828b0d-369e-4b11-a54a-ca06f3d5c6a5": "DEAD",
        "29de76c9-8ee6-4ad2-b362-56af9638a73b": "EAD Proceedings",
        "e576b1d0-bc89-452a-a93b-db05f5c7fb7a": "Escalaciones Deadlines",
        "be180812-786f-4c8c-b824-34e5862f3708": "Inventory 2024-2025",
        "4ea6810f-7811-4929-b8b1-4dadbbdcc749": "Master Escalations",
        "0c27e50e-cfc8-48cf-996d-822e5943f86c": "MENDOZA PROJECTS",
        "2a883fcd-875b-4797-8a8b-24981dbc9ba7": "OPERATIONS PROJECTS",
        "5abe75ce-26d7-4113-9e95-8b6001372bec": "Organico",
        "915f85e4-935f-4253-867f-a5630a0d49bb": "P+ SEND TO USCIS",
        "f75e38e5-ddd5-4153-8966-d644b61dc488": "Reasignación",
        "a3a772af-730e-4841-a978-0224462dbf69": "Reasignment",
        "dbfbf06f-22b4-4272-8992-19d24624d209": "Rejections other Forms",
        "86eab717-6b38-4ede-a354-5195f1ddcd1b": "SALES PROJECTS",
        "2af0ed12-cf5f-418b-89d3-e4b481d1b240": "VAWA P+",
    },
    # 🔖 Label Type
    "a42586d8-4725-401e-82cb-55a753496769": {
        "bba64821-1fff-4328-aad5-94fc0154f711": "Only DCL",
        "0890c6b6-4671-42c2-8c60-848fb04aa636": "Full CR",
        "4e2ff019-128e-4e14-ae6b-14fcee33e8bd": "N/A",
        "eda9c323-841d-4425-9d40-3cd037bb667a": "Other Forms CR",
    },
    # Case Review Status
    "f4d84c6d-8993-4282-8e68-3f2b96ea71e6": {
        "35093e4d-c52c-4406-9fe9-4ebdedde7f30": "CR NOT REQUIRE",
        "99d95692-c081-44fa-af51-356bc8d70d7d": "NEED CR",
        "35c1f72f-2afd-48c8-a2e2-e1d10f1a44b2": "CR IN PROGRESS",
        "ea20c72a-160a-483e-bf12-eec917872e0e": "DONE CR",
    },
}


class AssignmentService:
    ID_MAP = {
        "298c4ec5-05e3-432e-82da-cc973c44be54": "abogado_asignado",
        "a1c9d406-838f-48c6-b92c-a25992494b62": "proyecto",
        "a42586d8-4725-401e-82cb-55a753496769": "label_type",
        "f4d84c6d-8993-4282-8e68-3f2b96ea71e6": "case_review_status",
        "41889f31-5122-4400-8808-33ded3812d37": "open_case_type",
        "6301c50f-5047-4276-98d3-526d5c6b43ea": "rapsheet_status",
        "15182f5c-d7f8-4c6a-8184-f2c045ef1d21": "link_audio_cr",
        "2c04aa55-b609-4500-9281-0249f20ba594": "link_google_meet",
        "7e08a457-b45c-45f3-bff7-fbb6f1b7eb47": "link_decl_spanish",
        "6ac492a9-047d-4ba9-b7ae-f04c10994b0c": "cover_letter_link",
        "0b8868ab-d3ad-4c3b-b89e-209cb3c31836": "p_plus_filed_copy",
        "388a98e2-bf68-4160-b035-c960f77cb8f9": "cr_done_date",
        "c34dc8d7-fcd1-408a-94d6-35072c6c7fdf": "date_status_signed",
        "b1a419d5-6ba2-4d14-826f-530c1378442f": "fecha_asignacion",
        "a4087fc1-3e54-4f65-acc0-1c2fbcc6fc37": "open_case_date",
        "11aa750a-c424-4059-8945-e501dc132ee2": "deadline_statute",
        "7fbaba79-f396-4131-8737-c9990d717677": "packet_ready_cr",
        "a2e28dca-9b21-4704-b999-e5a1fd557866": "caso_resometer",
        "7609ea7c-eea0-4944-a6fa-22cedde72b14": "id_cliente",
        "a4362bff-2ce5-43a8-a344-a6895186a08c": "mycase_link",
        "2b1227a6-691e-4818-bf30-4acea5ca1b4e": "antiguos_attorney"
    }

    @staticmethod
    def transform_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma el JSON de ClickUp al formato de nuestra DB."""
        
        # 1. Campos de Sistema
        result = {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "status": task_data.get("status", {}).get("status"),
            "list_name": task_data.get("list", {}).get("name"),
            "folder_name": task_data.get("folder", {}).get("name"),
            "space_name": task_data.get("space", {}).get("name"),
            "priority": task_data.get("priority", {}).get("priority") if task_data.get("priority") else None,
            "date_created": LeadService._parse_clickup_date(task_data.get("date_created")),
            "date_updated": LeadService._parse_clickup_date(task_data.get("date_updated")),
            "date_closed": LeadService._parse_clickup_date(task_data.get("date_closed")),
            "date_done": LeadService._parse_clickup_date(task_data.get("date_done")),
            "due_date": LeadService._parse_clickup_date(task_data.get("due_date")),
            "task_content": task_data.get("description") or task_data.get("text_content"),
            "raw_data": task_data
        }

        # 2. Procesar Custom Fields por ID
        creator = task_data.get("creator", {})
        result["created_by"] = creator.get("username") if creator else None

        # Procesar Asignados (Unir múltiples nombres en un string)
        assignees = task_data.get("assignees", [])
        result["assignee"] = ", ".join(
            filter(None, [a.get("username") or a.get("email", "") for a in assignees])
        ) or None
            
        custom_fields = task_data.get("custom_fields", [])
        for field in custom_fields:
            f_id = field.get("id")
            if f_id in AssignmentService.ID_MAP:
                col_name = AssignmentService.ID_MAP[f_id]
                val = field.get("value")
                
                # Lógica de casteo según tipo de ClickUp
                f_type = field.get("type")
                if f_type == "date" and val:
                    result[col_name] = LeadService._parse_clickup_date(val)
                elif f_type == "checkbox":
                    result[col_name] = val is True or val == "true"
                elif f_type in ("drop_down", "labels"):
                    option_map = FIELD_OPTION_LABELS.get(f_id, {})
                    if isinstance(val, list):
                        # Labels puede traer múltiples opciones como lista de IDs
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