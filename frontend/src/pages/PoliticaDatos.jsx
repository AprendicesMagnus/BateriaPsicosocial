import { Link } from "react-router-dom";
import { RESPONSABLE_DATOS, POLITICA_DATOS } from "../utils/responsableDatos";
import "../styles/PoliticaDatos.css";

const CAMPOS_RESPONSABLE = [
  ["razonSocial", "Razón social"],
  ["nit", "NIT"],
  ["domicilio", "Domicilio"],
  ["direccion", "Dirección"],
  ["telefono", "Teléfono"],
  ["correo", "Correo electrónico"],
  ["contacto", "Persona encargada de peticiones, consultas y reclamos"],
];

export default function PoliticaDatos() {
  const campos = CAMPOS_RESPONSABLE.filter(([clave]) => Boolean(RESPONSABLE_DATOS[clave]));
  const { correo, direccion, domicilio } = RESPONSABLE_DATOS;

  return (
    <div className="politica">
      <main className="politica__tarjeta">
        <Link to="/" className="politica__volver">Volver al inicio</Link>
        <h1 className="politica__titulo">Política de tratamiento de datos personales</h1>
        <p className="politica__version">
          Versión {POLITICA_DATOS.version} · Vigente desde {POLITICA_DATOS.vigenteDesde}
        </p>

        <section className="politica__seccion">
          <h2>1. Responsable del tratamiento</h2>
          <dl className="politica__datos">
            {campos.map(([clave, etiqueta]) => (
              <div key={clave} style={{ display: "contents" }}>
                <dt>{etiqueta}</dt>
                <dd>{RESPONSABLE_DATOS[clave]}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="politica__seccion">
          <h2>2. Marco normativo</h2>
          <p>
            Esta política se adopta en cumplimiento de la Ley Estatutaria 1581 de 2012 y del Decreto 1074 de 2015
            (Capítulo 25, que compiló el Decreto 1377 de 2013). La aplicación de la Batería de Instrumentos para la
            Evaluación de Factores de Riesgo Psicosocial se rige por la Resolución 2646 de 2008 y por la Resolución
            2764 de 2022 del Ministerio del Trabajo.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>3. Datos personales que se tratan</h2>
          <ul>
            <li>Datos de la cuenta: nombre, apellido, correo electrónico, rol, contraseña (almacenada de forma protegida), número de resolución cuando el rol es Psicólogo y foto de perfil si la agregas.</li>
            <li>Datos de las empresas y áreas registradas en la plataforma.</li>
            <li>Ficha de datos generales, respuestas a los cuestionarios de la batería (intralaboral, extralaboral y estrés) y los resultados calculados a partir de ellas. Las respuestas se almacenan cifradas.</li>
            <li>Constancia del consentimiento informado: fecha, hora, dirección IP y versión del texto aceptado.</li>
            <li>Compras de baterías y pedidos de productos: referencias, valores y estado del pago. Los datos de pago son procesados directamente por Wompi.</li>
            <li>Mensajes enviados al Centro de ayuda y registros de auditoría de accesos y acciones en la plataforma.</li>
          </ul>
          <p>
            Algunos de estos datos, como la ficha de datos generales y las respuestas y resultados de la batería,
            pueden ser datos sensibles en los términos del artículo 5 de la Ley 1581 de 2012, porque pueden estar
            relacionados con la salud o afectar la intimidad del titular. La respuesta a las preguntas que versen
            sobre datos sensibles es facultativa.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>4. Finalidades del tratamiento</h2>
          <ul>
            <li>Crear y administrar cuentas, autenticar usuarios y enviar códigos de verificación y avisos por correo electrónico.</li>
            <li>Aplicar la batería, calificar los cuestionarios, generar indicadores e informes individuales y agrupados, y apoyar la identificación, evaluación y prevención de factores de riesgo psicosocial en la empresa.</li>
            <li>Gestionar compras, pedidos y pagos.</li>
            <li>Atender los mensajes del Centro de ayuda y las solicitudes para ejercer los derechos del titular.</li>
            <li>Mantener la seguridad, la trazabilidad y la verificación de autenticidad de los informes.</li>
            <li>Cumplir las obligaciones legales aplicables.</li>
          </ul>
          <p>Los datos no se utilizan para finalidades distintas de las descritas.</p>
        </section>

        <section className="politica__seccion">
          <h2>5. Acceso a los datos y custodia de los resultados</h2>
          <p>
            Los resultados individuales solo son accesibles para los roles autorizados: el Psicólogo (Evaluador SST)
            y el Responsable SST de la empresa evaluada, y el Super Administrador de la plataforma. Los usuarios con
            rol Jefe o Administrador acceden únicamente a información agrupada y no ven resultados individuales. Para
            proteger el anonimato, la plataforma no muestra resultados de grupos de menos de cinco personas.
          </p>
          <p>
            Conforme al artículo 5 de la Resolución 2764 de 2022, la custodia de los instrumentos de evaluación y de
            los informes individuales corresponde al profesional de psicología que aplica la batería, quien debe
            garantizar su reserva y confidencialidad y archivarlos según las normas de historia clínica. El empleador
            o contratante no puede conservar copia de los instrumentos ni de los informes individuales en la hoja de
            vida del trabajador, y los informes consolidados por grupos solo pueden utilizarse para la intervención de
            los factores de riesgo psicosocial. {RESPONSABLE_DATOS.razonSocial} es el responsable del tratamiento de
            los datos que se registran en la plataforma y no sustituye al psicólogo en su función de custodia.
          </p>
          <p>
            Para operar el servicio se usan proveedores que tratan datos por cuenta de la plataforma: Wompi para los
            pagos, Google para el inicio de sesión opcional con Google y un servicio de correo electrónico para los
            códigos y avisos. Cada proveedor trata los datos conforme a sus propias políticas. La plataforma controla
            el acceso por roles y registra en una auditoría las acciones relevantes.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>6. Derechos del titular</h2>
          <p>Como titular de los datos personales tienes derecho a:</p>
          <ul>
            <li>Conocer, actualizar y rectificar tus datos personales frente al responsable y los encargados del tratamiento, incluso cuando sean parciales, inexactos, incompletos, fraccionados, induzcan a error, o su tratamiento esté prohibido o no haya sido autorizado.</li>
            <li>Solicitar prueba de la autorización otorgada, salvo cuando la ley la exceptúe como requisito para el tratamiento.</li>
            <li>Ser informado, previa solicitud, sobre el uso que se ha dado a tus datos personales.</li>
            <li>Presentar quejas ante la Superintendencia de Industria y Comercio por infracciones a la ley.</li>
            <li>Revocar la autorización y/o solicitar la supresión del dato cuando en el tratamiento no se respeten los principios, derechos y garantías constitucionales y legales, en los términos del artículo 8 de la Ley 1581 de 2012.</li>
            <li>Acceder en forma gratuita a tus datos personales que hayan sido objeto de tratamiento. Puedes consultarlos gratuitamente al menos una vez cada mes calendario y cada vez que haya modificaciones sustanciales de esta política que motiven nuevas consultas.</li>
          </ul>
          <p>
            Estos derechos pueden ser ejercidos por el titular, quien debe acreditar su identidad; por sus
            causahabientes; por su representante o apoderado, previa acreditación de la representación; o por
            estipulación a favor de otro o para otro.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>7. Cómo ejercer tus derechos</h2>
          <p>Puedes presentar tu consulta o reclamo por cualquiera de estos canales:</p>
          <ul>
            <li>Desde la plataforma, con la sesión iniciada: escribe en el <Link to="/soporte">Centro de ayuda</Link> indicando que se trata de una solicitud sobre tus datos personales.</li>
            {correo && (
              <li>Por correo electrónico a <a href={`mailto:${correo}`}>{correo}</a>.</li>
            )}
            {direccion && (
              <li>Por escrito, en la dirección {direccion}{domicilio ? `, ${domicilio}` : ""}.</li>
            )}
          </ul>
          <p>Dejaremos constancia de la recepción y del trámite de cada solicitud. Para proteger tus datos podremos pedirte que acredites tu identidad.</p>
          <h3>Consultas</h3>
          <p>
            Las consultas se atienden en un máximo de diez (10) días hábiles contados desde la fecha de su recibo.
            Si no es posible atenderlas en ese término, te informaremos los motivos de la demora y la fecha en que
            se atenderá, que no podrá superar los cinco (5) días hábiles siguientes al vencimiento del primer término.
          </p>
          <h3>Reclamos</h3>
          <p>
            Si consideras que tus datos deben corregirse, actualizarse o suprimirse, o adviertes un presunto
            incumplimiento de los deberes de la ley, presenta un reclamo con tu identificación, la descripción de los
            hechos, tu dirección y los documentos que quieras hacer valer. Si el reclamo está incompleto, te
            requeriremos dentro de los cinco (5) días siguientes a su recepción para que lo subsanes; si pasan dos
            (2) meses sin que presentes la información requerida, se entenderá que desististe del reclamo. Una vez
            completo, se incluirá la leyenda &quot;reclamo en trámite&quot; en un máximo de dos (2) días hábiles y se
            atenderá en un máximo de quince (15) días hábiles contados desde el día siguiente a su recibo. Si no es
            posible, te informaremos los motivos de la demora y la fecha de respuesta, que no podrá superar los ocho
            (8) días hábiles siguientes al vencimiento del primer término.
          </p>
          <h3>Queja ante la Superintendencia de Industria y Comercio</h3>
          <p>
            Solo podrás presentar una queja ante la Superintendencia de Industria y Comercio una vez hayas agotado
            el trámite de consulta o reclamo ante el responsable del tratamiento.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>8. Autorización</h2>
          <p>
            Quien crea una cuenta debe leer y aceptar esta política; la aceptación queda registrada con su fecha y la
            versión aceptada. Las personas que responden la batería mediante un enlace compartido por su psicólogo,
            sin crear cuenta, otorgan su autorización a través del consentimiento informado que se les presenta antes
            de comenzar; ese consentimiento queda registrado con su fecha, hora, dirección IP y versión del texto.
          </p>
        </section>

        <section className="politica__seccion">
          <h2>9. Vigencia y cambios</h2>
          <p>
            Esta política rige desde la fecha indicada al inicio de la página. Cualquier cambio sustancial se
            comunicará a los titulares antes de implementar la nueva política. La base de datos de la plataforma
            estará vigente mientras se preste el servicio y subsistan las finalidades descritas, y por el tiempo que
            exijan las normas aplicables, incluidas las relativas a la conservación de la historia clínica
            ocupacional.
          </p>
        </section>
      </main>
    </div>
  );
}
