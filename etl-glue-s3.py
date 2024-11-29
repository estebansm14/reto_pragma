import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.gluetypes import *
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
from pyspark.sql import functions as SqlFuncs

def _find_null_fields(ctx, schema, path, output, nullStringSet, nullIntegerSet, frame):
    if isinstance(schema, StructType):
        for field in schema:
            new_path = path + "." if path != "" else path
            output = _find_null_fields(ctx, field.dataType, new_path + field.name, output, nullStringSet, nullIntegerSet, frame)
    elif isinstance(schema, ArrayType):
        if isinstance(schema.elementType, StructType):
            output = _find_null_fields(ctx, schema.elementType, path, output, nullStringSet, nullIntegerSet, frame)
    elif isinstance(schema, NullType):
        output.append(path)
    else:
        x, distinct_set = frame.toDF(), set()
        for i in x.select(path).distinct().collect():
            distinct_ = i[path.split('.')[-1]]
            if isinstance(distinct_, list):
                distinct_set |= set([item.strip() if isinstance(item, str) else item for item in distinct_])
            elif isinstance(distinct_, str) :
                distinct_set.add(distinct_.strip())
            else:
                distinct_set.add(distinct_)
        if isinstance(schema, StringType):
            if distinct_set.issubset(nullStringSet):
                output.append(path)
        elif isinstance(schema, IntegerType) or isinstance(schema, LongType) or isinstance(schema, DoubleType):
            if distinct_set.issubset(nullIntegerSet):
                output.append(path)
    return output

def drop_nulls(glueContext, frame, nullStringSet, nullIntegerSet, transformation_ctx) -> DynamicFrame:
    nullColumns = _find_null_fields(frame.glue_ctx, frame.schema(), "", [], nullStringSet, nullIntegerSet, frame)
    return DropFields.apply(frame=frame, paths=nullColumns, transformation_ctx=transformation_ctx)

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Script generated for node Amazon S3
AmazonS3_node1732830590502 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ";", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://retopragmadatalakearchivos/raw/"], "recurse": True}, transformation_ctx="AmazonS3_node1732830590502")

# Script generated for node Change Schema
ChangeSchema_node1732830880603 = ApplyMapping.apply(frame=AmazonS3_node1732830590502, mappings=[("tipo_identificacion", "string", "tipo_identificacion", "string"), ("identificacion", "string", "identificacion", "bigint"), ("nombre", "string", "nombre", "string"), ("ciudad", "string", "ciudad", "string"), ("fecha_carga", "string", "fecha_carga", "date"), ("nombre_proveedor", "string", "nombre_proveedor", "string"), ("tipo_energia", "string", "tipo_energia", "string"), ("estado_proveedor", "string", "estado_proveedor", "string"), ("capacidad_mw", "string", "capacidad_mw", "string"), ("tipo_transaccion", "string", "tipo_transaccion", "string"), ("nombre_cliente", "string", "nombre_cliente", "string"), ("producto", "string", "producto", "string"), ("cantidad_comprada", "string", "cantidad_comprada", "int"), ("precio", "string", "precio", "int")], transformation_ctx="ChangeSchema_node1732830880603")

# Script generated for node Drop Duplicates
DropDuplicates_node1732831039059 =  DynamicFrame.fromDF(ChangeSchema_node1732830880603.toDF().dropDuplicates(), glueContext, "DropDuplicates_node1732831039059")

# Script generated for node Drop Null Fields
DropNullFields_node1732831134542 = drop_nulls(glueContext, frame=DropDuplicates_node1732831039059, nullStringSet={"", "null"}, nullIntegerSet={-1}, transformation_ctx="DropNullFields_node1732831134542")

# Script generated for node Amazon S3
AmazonS3_node1732831181945 = glueContext.getSink(path="s3://retopragmadatalakearchivos/processed/", connection_type="s3", updateBehavior="UPDATE_IN_DATABASE", partitionKeys=["fecha_carga"], enableUpdateCatalog=True, transformation_ctx="AmazonS3_node1732831181945")
AmazonS3_node1732831181945.setCatalogInfo(catalogDatabase="db-reto-pragma",catalogTableName="tbl_transaccional")
AmazonS3_node1732831181945.setFormat("glueparquet", compression="snappy")
AmazonS3_node1732831181945.writeFrame(DropNullFields_node1732831134542)
job.commit()